#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import datetime
import six

from bson import ObjectId
import geojson
import numpy
from PIL import Image as PIL_Image, ImageDraw as PIL_ImageDraw

from girder import events
from girder.constants import AccessType
from girder.models.model_base import Model, GirderException, ValidationException

from .segmentation_helpers import ScikitSegmentationHelper, \
    OpenCVSegmentationHelper


class Segmentation(Model):
    class Skill(object):
        NOVICE = 'novice'
        EXPERT = 'expert'

    def initialize(self):
        self.name = 'segmentation'
        self.ensureIndices(['imageId', 'created'])

        self.exposeFields(AccessType.READ, [
            'imageId',
            'skill',
            'creatorId',
            'created'
        ])
        self.summaryFields = ['_id', 'imageId', 'skill']
        events.bind('model.item.remove_with_kwargs',
                    'isic_archive.gc_segmentation',
                    self._onDeleteItem)

    def doSegmentation(self, image, seedCoord, tolerance):
        """
        Run a lesion segmentation.

        :param image: A Girder Image item.
        :param seedCoord: X, Y coordinates of the segmentation seed point.
        :type seedCoord: tuple[int]
        :param tolerance: The intensity tolerance value for the segmentation.
        :type tolerance: int
        :return: The lesion segmentation, as a GeoJSON Polygon Feature.
        :rtype: geojson.Feature
        """
        imageData = self.model('image', 'isic_archive').imageData(image)

        if not(
            # The imageData has a shape of (rows, cols), the seed is (x, y)
            0.0 <= seedCoord[0] <= imageData.shape[1] and
            0.0 <= seedCoord[1] <= imageData.shape[0]
        ):
            raise GirderException('seedCoord is out of bounds')

        # OpenCV is significantly faster at segmentation right now
        contourCoords = OpenCVSegmentationHelper.segment(
            imageData, seedCoord, tolerance)

        contourFeature = geojson.Feature(
            geometry=geojson.Polygon(
                coordinates=(contourCoords.tolist(),)
            ),
            properties={
                'source': 'autofill',
                'seedPoint': seedCoord,
                'tolerance': tolerance
            }
        )
        return contourFeature

    def createSegmentation(self, image, skill, creator, lesionBoundary):
        now = datetime.datetime.utcnow()
        segmentation = self.save({
            'imageId': image['_id'],
            'skill': skill,
            'creatorId': creator['_id'],
            'lesionBoundary': lesionBoundary,
            'created': now
        })
        return segmentation

    def createRasterSegmentation(self, image, skill, creator, mask):
        File = self.model('file')
        Upload = self.model('upload')

        now = datetime.datetime.utcnow()

        if len(mask.shape) != 2:
            raise ValidationException('Mask must be a single-channel image.')
        if mask.shape != (
                image['meta']['acquisition']['pixelsY'],
                image['meta']['acquisition']['pixelsX']):
            raise ValidationException(
                'Mask must have the same dimensions as the image.')
        if mask.dtype != numpy.uint8:
            raise ValidationException('Mask may only contain 8-bit values.')
        # TODO: validate that only a single contiguous region is present

        maskOutputStream = ScikitSegmentationHelper.writeImage(
            mask, encoding='png')

        segmentation = self.save({
            'imageId': image['_id'],
            'skill': skill,
            'creatorId': creator['_id'],
            'created': now
        })

        maskFile = Upload.uploadFromFile(
            obj=maskOutputStream,
            size=len(maskOutputStream.getvalue()),
            name='%s_segmentation.png' % (image['name']),
            parentType=None,
            parent=None,
            user=creator,
            mimeType='image/png',
        )
        maskFile['attachedToId'] = segmentation['_id']
        maskFile['attachedToType'] = ['segmentation', 'isic_archive']
        maskFile = File.save(maskFile)

        segmentation['maskId'] = maskFile['_id']
        segmentation = self.save(segmentation)

        return segmentation

    def maskFile(self, segmentation):
        File = self.model('file')
        return File.load(segmentation['maskId'], force=True, exc=True)

    def mask(self, segmentation, image=None):
        Image = self.model('image', 'isic_archive')
        if not image:
            image = Image.load(segmentation['imageId'], force=True, exc=True)

        segmentationMask = ScikitSegmentationHelper._contourToMask(
            numpy.zeros(Image.imageData(image).shape),
            segmentation['lesionBoundary']['geometry']['coordinates'][0]
        ).astype(numpy.uint8)
        segmentationMask *= 255

        return segmentationMask

    def renderedMask(self, segmentation, image=None):
        segmentationMask = self.mask(segmentation, image)
        return ScikitSegmentationHelper.writeImage(segmentationMask, 'png')

    def boundaryThumbnail(self, segmentation, image=None, width=256):
        Image = self.model('image', 'isic_archive')
        if not image:
            image = Image.load(segmentation['imageId'], force=True, exc=True)

        pilImageData = PIL_Image.fromarray(Image.imageData(image))
        pilDraw = PIL_ImageDraw.Draw(pilImageData)
        pilDraw.line(
            list(six.moves.map(tuple,
                               segmentation['lesionBoundary']
                                           ['geometry']['coordinates'][0])),
            fill=(0, 255, 0),  # TODO: make color an option
            width=5
        )

        return ScikitSegmentationHelper.writeImage(
            numpy.asarray(pilImageData), 'jpeg', width)

    def _onDeleteItem(self, event):
        item = event.info['document']
        # TODO: can we tell if this item is an image?
        for segmentation in self.find({
            'imageId': item['_id']
        }):
            self.remove(segmentation, **event.info['kwargs'])

    def remove(self, segmentation, **kwargs):
        File = self.model('file')
        if 'maskId' in segmentation:
            File.remove(self.maskFile(segmentation))
        super(Segmentation, self).remove(segmentation, **kwargs)

    def validate(self, doc):
        try:
            assert set(six.viewkeys(doc)) >= {
                'imageId', 'skill', 'creatorId', 'created'}
            assert set(six.viewkeys(doc)) <= {
                '_id', 'imageId', 'skill', 'creatorId', 'created',
                'maskId', 'lesionBoundary'}

            assert isinstance(doc['imageId'], ObjectId)
            assert self.model('image', 'isic_archive').find(
                {'_id': doc['imageId']}).count()

            assert doc['skill'] in {self.Skill.NOVICE, self.Skill.EXPERT}

            assert isinstance(doc['creatorId'], ObjectId)
            assert self.model('user', 'isic_archive').find(
                {'_id': doc['creatorId']}).count()

            assert isinstance(doc['created'], datetime.datetime)

            if 'lesionBoundary' not in doc:
                return doc
            assert isinstance(doc['lesionBoundary'], dict)
            assert set(six.viewkeys(doc['lesionBoundary'])) == {
                'type', 'properties', 'geometry'}

            assert doc['lesionBoundary']['type'] == 'Feature'

            assert isinstance(doc['lesionBoundary']['properties'], dict)
            assert set(six.viewkeys(doc['lesionBoundary']['properties'])) <= {
                'source', 'startTime', 'stopTime', 'seedPoint', 'tolerance'}
            assert set(six.viewkeys(doc['lesionBoundary']['properties'])) >= {
                'source', 'startTime', 'stopTime'}
            assert doc['lesionBoundary']['properties']['source'] in {
                'autofill', 'manual pointlist'}
            assert isinstance(doc['lesionBoundary']['properties']['startTime'],
                              datetime.datetime)
            assert isinstance(doc['lesionBoundary']['properties']['stopTime'],
                              datetime.datetime)

            assert isinstance(doc['lesionBoundary']['geometry'], dict)
            assert set(six.viewkeys(doc['lesionBoundary']['geometry'])) == {
                'type', 'coordinates'}
            assert doc['lesionBoundary']['geometry']['type'] == 'Polygon'
            assert isinstance(doc['lesionBoundary']['geometry']['coordinates'],
                              list)
            assert len(doc['lesionBoundary']['geometry']['coordinates']) == 1
            assert isinstance(
                doc['lesionBoundary']['geometry']['coordinates'][0], list)
            assert len(doc['lesionBoundary']['geometry']['coordinates'][0]) > 2
            assert doc['lesionBoundary']['geometry']['coordinates'][0][0] == \
                doc['lesionBoundary']['geometry']['coordinates'][0][-1]
            for coord in doc['lesionBoundary']['geometry']['coordinates'][0]:
                assert isinstance(coord, list)
                assert len(coord) == 2
                for val in coord:
                    assert isinstance(val, (int, float))
                    assert val >= 0

        except (AssertionError, KeyError):
            # TODO: message
            raise ValidationException('')
        return doc
