import $ from 'jquery';
import _ from 'underscore';

import {getApiRoot} from 'girder/rest';

import SegmentationsDisplayView from './SegmentationsDisplayView';
import ImageFullscreenWidget from '../../common/Viewer/ImageFullscreenWidget';
import View from '../../view';

import ImageDetailsPageTemplate from './imageDetailsPage.pug';
import './imageDetailsPage.styl';

const ImageDetailsPane = View.extend({
    events: {
        'click #isic-image-details-zoom': 'zoom',
        'click #isic-image-details-close': 'closeDetails'
    },

    /**
     * @param {ImageModel} settings.image
     */
    initialize: function (settings) {
        this.image = settings.image;

        if (!this.image.has('meta')) {
            // If the image is only a summary, fetch details, then render
            // Since this view doesn't own the "image", "listenTo" absolutely must be used
            this.listenTo(this.image, 'g:fetched', this.render);
            this.image.fetch();
            // TODO: a loading widget could be displayed while the fetch runs
        } else {
            this.render();
        }
    },

    render: function () {
        // Get image data
        let created = this.formatDate(this.image.get('created'));

        // Get license, default to CC-0
        let license;
        if (this.image.has('license')) {
            license = {
                name: this.image.get('license'),
                url: null
            };
        } else {
            license = {
                name: 'CC-0',
                url: 'https://creativecommons.org/publicdomain/zero/1.0/'
            };
        }

        this.$el.html(ImageDetailsPageTemplate({
            _: _,
            apiRoot: getApiRoot(),
            image: this.image,
            created: created,
            license: license
        }));

        this.segmentationsDisplayView = new SegmentationsDisplayView({
            image: this.image,
            el: this.$('#isic-image-details-segmentations-display-view-container'),
            parentView: this
        });

        return this;
    },

    zoom: function () {
        new ImageFullscreenWidget({ // eslint-disable-line no-new
            el: $('#g-dialog-container'),
            model: this.image,
            parentView: this
        }).render();
    },

    closeDetails: function () {
        this.image.deselect();
    }
});

export default ImageDetailsPane;
