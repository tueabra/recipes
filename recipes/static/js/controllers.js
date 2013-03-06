function ListCtrl($scope, $rootScope, Recipe) {
    $scope.root = $rootScope;

    $scope.recipes = [];
    Recipe.query(function(data) {
       $scope.recipes = data.objects; 
    });

    function resizeRecipes() {
        var width = ($("#content").innerWidth() - 15);
        var precise = width / 220;
        var ceil = Math.ceil(precise);
        var rounded = width / ceil;
        var floor = Math.floor(rounded);

        $('.recipe:not(.favorite)').animate({ width: floor }, 'fast');
        $('.recipe.favorite').animate({ width: (floor * 2) }, 'fast');
    }

    $scope.getWidth = function() {
        return $(window).width();
    };
    $scope.$watch($scope.getWidth, resizeRecipes);
    window.onresize = function(){
        $scope.$apply();
    }

    setTimeout(resizeRecipes, 100);

    $scope.matchesFilter = function(recipe) {
        var filter = $scope.root.filter.trim().toLowerCase();
        if(filter == '') return true;

        if(recipe.name && recipe.name.toLowerCase().indexOf(filter) != -1)
            return true;

        for(var tag in recipe.tags)
            if(recipe.tags[tag].name && recipe.tags[tag].name.toLowerCase().indexOf(filter) != -1)
                return true;

        return false;
    }
}

function EditRecipeCtrl($scope, $routeParams, $location, $filter, Recipe, Garniture) {

    function saveGarniture() {
        var ids = [];
        for(var i in $scope.garnitures)
            ids.push($scope.garnitures[i]['id'] || $scope.garnitures[i]['value']);
        Garniture.save({ id: $routeParams.id, ids: ids });
    }
    function setImage() {
        var file = $('input[name="image"]').get(0).files[0];
        if(!file) return;
        var fd = new FormData()
        fd.append("image", file);
        fd.append("id", $scope.recipe.id);
        var xhr = new XMLHttpRequest()
        xhr.open("POST", "/api/set-image/")
        xhr.send(fd);
    }
    function cleanRecipe() {
        var timings = [];
        for(var i in $scope.recipe.timings)
            if($scope.recipe.timings[i].description || $scope.recipe.timings[i].minutes)
                timings.push($scope.recipe.timings[i]);
        $scope.recipe.timings = timings;

        var ingredients = [];
        for(var i in $scope.recipe.ingredients)
            if($scope.recipe.ingredients[i].amount || $scope.recipe.ingredients[i].name)
                ingredients.push($scope.recipe.ingredients[i]);
        $scope.recipe.ingredients = ingredients;
    }

    /* Edit existing recipe */
    if($routeParams.id) {

        $scope.recipe = Recipe.get({id: $routeParams.id}, function() {
            if($scope.recipe.tags.length == 0)
                $scope.recipe.tags.push({});
            if($scope.recipe.timings.length == 0)
                $scope.recipe.timings.push({});
            if($scope.recipe.ingredients.length == 0)
                $scope.recipe.ingredients.push({});
        });

        $scope.Save = function() {
            saveGarniture();
            cleanRecipe();
            $scope.recipe.$save(function() {
                setImage();
                $location.path("/recipe/"+$scope.recipe.id);
            });
        }

        Garniture.query({ id: $routeParams.id }, function(data) {
            $scope.garnitures = data.objects;
        });

    /* Add new recipe */
    } else {

        $scope.recipe = new Recipe({
            tags: [{}],
            timings: [{}],
            ingredients: [{}]
        });
        $scope.garnitures = [];
        $scope.Save = function() {
            cleanRecipe();
            $scope.recipe.$add(function() {
                saveGarniture();
                setImage();
                $location.path("/recipe/"+$scope.recipe.id);
            });
        }

    }

    $scope.temporaryImage = '';

    $scope.Delete = function() {
        if(confirm('Vil du virkelig slette denne opskrift?')) {
            $scope.recipe.$delete();
            $location.path("/");
        }
    }

    $scope.ensureCapitalized = function(object, key) {
        object[key] = object[key].capitalize();
    }

    $scope.ensureEmptyInput = function(type, keys, selector) {
        /* Ensure the only empty input is at the bottom */
        for(var i = $scope.recipe[type].length-2 ; i >= 0 ; i--) {
            var cur = $scope.recipe[type][i];
            var full = ''
            for(var key in keys)
                full += cur[keys[key]] || '';
            if(full == '') {
                $scope.recipe[type].splice(i, 1);
                setTimeout(function() {
                    $(selector).last().focus();
                }, 100);
            }
        }

        /* Ensure we have an empty input at the bottom */
        var full = '';
        var last = $scope.recipe[type].slice(-1)[0];
        if(last) {
            for(var key in keys)
                full += last[keys[key]] || '';
            if(full != '')
                $scope.recipe[type].push({});
        }
    }

    $scope.ensureNumber = function(key) {
        $scope.recipe[key] = $scope.recipe[key].replace(/\D/, '');
    }

    $scope.uploadFile = function() {
        $('input[type="file"]').on('change', function() {
            var fd = new FormData()
            fd.append("image", this.files[0]);
            fd.append("id", $scope.recipe.id);
            var xhr = new XMLHttpRequest()
            xhr.open("POST", "/api/image-preview/")
            xhr.onreadystatechange = function() {
                if(xhr.readyState == 4) {
                    var b64 = $.parseJSON(xhr.responseText)['image'];
                    $scope.temporaryImage = 'data:image/png;base64,'+b64;
                    $scope.$apply();
                }
            }
            xhr.send(fd);
        }).click();
    }
}

function RecipeCtrl($scope, $routeParams, Recipe, Garniture, AsGarniture) {
    $scope.recipe = Recipe.get({id: $routeParams.id});

    Garniture.query({ id: $routeParams.id }, function(data) {
        $scope.garnitures = data.objects;
    });

    AsGarniture.query({ id: $routeParams.id }, function(data) {
        $scope.as_garniture = data.objects;
    });

    $scope.toggleFavorite = function() {
        $scope.recipe.favorite = ! $scope.recipe.favorite;
        $scope.recipe.$save();
    }

    $scope.toggleTried = function() {
        $scope.recipe.has_tried = ! $scope.recipe.has_tried;
        $scope.recipe.$save();
    }
}
