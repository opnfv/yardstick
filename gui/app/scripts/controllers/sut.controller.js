'use strict';

angular.module('yardStickGui2App')
    .controller('SUTController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, ngDialog) {


            init();
            $scope.showloading = false;
            $scope.loadingOPENrc = false;

            function init() {


                $scope.uuid = $stateParams.uuid;
                $scope.sutInfo = {};
                getItemIdDetail();
                getSUTDetail();

            }

            function getItemIdDetail() {
                mainFactory.ItemDetail().get({
                    'envId': $scope.uuid
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.envName = response.result.environment.name;
                    }else{
                        mainFactory.errorHandler1(response);
                    }
                }, function(error) {
                    mainFactory.errorHandler2(error);
                })
            }

            function getSUTDetail(){
                mainFactory.SUTDetail().get({
                    'envId': $scope.uuid
                }).$promise.then(function(resp){
                    $scope.sutInfo = resp.result.sut;
                    console.log($scope.sutInfo);
                }, function(error){
                })
            }

            $scope.goBack = function goBack() {
                $state.go('app.projectList');
            }


            $scope.goNext = function goNext() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.container', { uuid: $scope.uuid });
            }

        }
    ]);
