'use strict';

angular.module('Recipes.services', ['ngResource']).
  factory('Recipe', function($resource) {
    var Recipe = $resource('api/recipe/:id', {id: '@id'}, {
        query: { method: 'GET' },
        save: { method: 'PATCH' },
        add: { method: 'POST' }
    });
    Recipe.prototype.total_time = function() {
        var time = 0;
        for(var i in this.timings) {
            if(parseInt(this.timings[i].minutes))
                time += parseInt(this.timings[i].minutes);
        }
        return time;
    }
    return Recipe;
  }).
  factory('Garniture', function($resource) {
    return $resource('api/garniture/:id', {id: '@id'}, {
        query: { method: 'GET' }
    });
  }).
  factory('AsGarniture', function($resource) {
    return $resource('api/as-garniture/:id', {id: '@id'}, {
        query: { method: 'GET' }
    });
  });
