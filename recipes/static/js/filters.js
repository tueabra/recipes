'use strict';

angular.module('Recipes.filters', []).
    filter('translate', function() {
        return function(input) {
            if(typeof(locales) == "undefined") /* default to english */
                return input;
            if(!locales[input])
                throw "Missing translation";
            return locales[input];
        }
    });
