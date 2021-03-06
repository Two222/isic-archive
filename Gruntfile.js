/**
 * Copyright 2016 Kitware Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
const path = require('path');

module.exports = function (grunt) {
    var staticLibPath = path.resolve(
        grunt.config.get('staticDir'), 'built', 'plugins', 'isic_archive', 'libs');

    // Install and copy legacy resources for Angular app
    grunt.registerTask('isic_archive-legacy-bower-install', 'Install Bower packages', function () {
        var bower = require('bower');
        var done = this.async();
        bower.commands
            .install([
                'jquery#2.1.0',
                'underscore#~1.5',
                'flatstrap#3.1.1',
                'font-awesome#4.0.3',
                'angular#1.4.5',
                'angular-resource#1.4.5',
                'angular-ui-bootstrap-bower#0.14.3'
            ])
            .on('end', function (results) {
                done();
            })
            .on('error', function (results) {
                done(false);
            });
    });
    grunt.config.set('copy.isic_archive-legacy-libs-bower', {
        expand: true,
        nonull: true,
        cwd: 'bower_components',
        src: [
            'jquery/dist/jquery.min.js',
            'underscore/underscore-min.js',
            'bootstrap/dist/js/bootstrap.min.js',
            'bootstrap/dist/css/bootstrap.min.css',
            'bootstrap/dist/fonts/glyphicons-halflings-regular.woff',
            'bootstrap/dist/fonts/glyphicons-halflings-regular.ttf',
            'font-awesome/css/font-awesome.min.css',
            'font-awesome/fonts/fontawesome-webfont.ttf',
            'font-awesome/fonts/fontawesome-webfont.woff',
            'angular/angular.min.js',
            'angular-resource/angular-resource.min.js',
            'angular-bootstrap/ui-bootstrap-tpls.min.js'
        ],
        dest: staticLibPath
    });
    grunt.config.set('copy.isic_archive-legacy-libs-npm', {
        expand: true,
        nonull: true,
        cwd: 'node_modules',
        src: [
            'geojs/geo.min.js'
        ],
        dest: staticLibPath
    });
    grunt.registerTask('isic_archive-legacy', [
        // 'npm-install:isic_archive:false:bower@^1.8.0',
        'isic_archive-legacy-bower-install',
        'copy:isic_archive-legacy-libs-bower',
        'copy:isic_archive-legacy-libs-npm'
    ]);

    grunt.registerTask('isic_archive-web', [
        'isic_archive-legacy'
    ]);
};
