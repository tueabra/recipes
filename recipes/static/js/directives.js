'use strict';

function get_object(scope, expression) {
    /* Is this really the only way to do it? */
    var obj = scope;
    var parts = expression.split('.');
    for(var i in parts.slice(0, parts.length-1))
        obj = obj[parts[i]];
    return obj[parts[parts.length-1]];
}

angular.module('Recipes.directives', []).
    directive('autoComplete', function($timeout) {
        return function(scope, element, attrs) {
            element.autocomplete({
                source: function(request, response) {
                    $.getJSON(attrs.uiAutocompleteUrl, request, function(data) {
                        response(data.objects);   
                    });
                },
                select: function(event, ui) {
                    if(attrs.uiAutocompleteAdd) {
                        var obj = get_object(scope, attrs.uiAutocompleteAdd);
                        obj.push(ui.item);
                        element.val('');
                        scope.$apply();
                        return false;
                    }
                    $timeout(function() {
                      element.trigger('input');
                    }, 0);
                }
            });
        };
    }).
    directive('requireNumber', function() {
        return {
            restrict: 'A',
            link: function(scope, element, attrs) {
                scope.$watch(attrs.ngModel, function(value, old, $parent) {
                    if(value && value.replace) {
                        var obj = get_object(scope, attrs.ngModel);
                        obj = value.replace(/\D/, '');
                    }
                });
            }
        };
    });
