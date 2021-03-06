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

from girder.models.model_base import Model


class Batch(Model):
    def initialize(self):
        self.name = 'batch'
        # TODO: add indexes

    def createBatch(self, dataset, creator, signature):
        now = datetime.datetime.utcnow()

        batch = self.save({
            'datasetId': dataset['_id'],
            'created': now,
            'creatorId': creator,
            'signature': signature
        })
        return batch

    def validate(self, doc, **kwargs):
        # TODO: implement
        return doc
