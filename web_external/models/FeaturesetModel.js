import _ from 'underscore';

import {getCurrentUser} from 'girder/auth';

import Model from './Model';
import UserModel from './UserModel';

const FeaturesetModel = Model.extend({
    resourceName: 'featureset',

    /**
     * Get the name of the featureset.
     */
    name: function () {
        return `${this.get('name')} (version ${this.get('version')})`;
    },

    creator: function () {
        return new UserModel(this.get('creator'));
    },

    destroy: function (options) {
        // Don't modify the "options", but override some properties
        let params = _.clone(options);
        // Featureset deletion may fail if it's being used by a study
        params.wait = true;

        return Model.prototype.destroy.call(this, params);
    },

    canAdmin: function () {
        let user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default FeaturesetModel;
