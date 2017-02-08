isic.views.TermsAcceptanceView = isic.View.extend({
    events: {
        'click #isic-terms-accept': function (event) {
            // Disable buttons while request is pending
            var buttons = this.$('.isic-terms-agreement-button-container button');
            buttons.prop('disabled', true);

            if (girder.currentUser) {
                girder.currentUser.setAcceptTerms(function () {
                    // Refresh page
                    Backbone.history.loadUrl();
                });
            } else {
                window.sessionStorage.setItem('acceptTerms', 'true');
                Backbone.history.loadUrl();
            }
        },
        'click #isic-terms-reject': function (event) {
            // Route to home page
            isic.router.navigate('', {trigger: true});
        }
    },

    initialize: function () {
        this.termsOfUseWidget = new isic.views.TermsOfUseWidget({
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.termsAcceptancePage());

        this.termsOfUseWidget.setElement(
            this.$('#isic-terms-of-use-container')).render();

        return this;
    }
}, {
    // Static methods
    hasAcceptedTerms: function () {
        if (girder.currentUser) {
            return girder.currentUser.canAcceptTerms();
        } else {
            return window.sessionStorage.getItem('acceptTerms') === 'true';
        }
    }
});

isic.router.route('termsAcceptance', 'termsAcceptance', function () {
    girder.events.trigger('g:navigateTo', isic.views.TermsAcceptanceView);
});
