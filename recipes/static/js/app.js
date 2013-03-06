'use strict';

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

var Recipes = angular.module('Recipes', ['Recipes.services', 'Recipes.directives']).

    /* URL Routing */
    config(['$routeProvider', function($routeProvider) {
        $routeProvider.when('/', {templateUrl: '/static/partials/list.html', controller: ListCtrl});
        $routeProvider.when('/add', {templateUrl: '/static/partials/edit.html', controller: EditRecipeCtrl});
        $routeProvider.when('/recipe/:id', {templateUrl: '/static/partials/recipe.html', controller: RecipeCtrl});
        $routeProvider.when('/recipe/:id/edit', {templateUrl: '/static/partials/edit.html', controller: EditRecipeCtrl});
        $routeProvider.otherwise({redirectTo: '/'});
    }]);

Recipes.run(function($rootScope) {
    $rootScope.filter = '';

    $rootScope.getImage = function(recipe, as_object) {
        as_object = typeof(as_object) == 'undefined' ? true : as_object;
        var none = '/static/images/no-image.gif';
        try {
            var img = (recipe.image ? '/static/media/'+recipe.image : none);
        } catch(err) {
            var img = none;
        }
        if(as_object)
            return {'background-image': 'url('+img+')'};
        else
            return img;
    }
});