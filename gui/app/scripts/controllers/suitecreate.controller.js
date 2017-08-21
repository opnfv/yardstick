'use strict';

angular.module('yardStickGui2App')
    .controller('suitcreateController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog) {


            init();


            function init() {

                getTestcaseList();
                $scope.constructTestSuit = constructTestSuit;
                $scope.openDialog = openDialog;
                $scope.createSuite = createSuite;

            }

            function getTestcaseList() {
                mainFactory.getTestcaselist().get({

                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.testcaselist = response.result;


                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            $scope.testsuiteList = [];
            $scope.suitReconstructList = [];

            function constructTestSuit(name) {

                var index = $scope.testsuiteList.indexOf(name);
                if (index > -1) {
                    $scope.testsuiteList.splice(index, 1);
                } else {
                    $scope.testsuiteList.push(name);
                }


                $scope.suitReconstructList = $scope.testsuiteList;

            }

            function createSuite(name) {
                mainFactory.suiteCreate().post({
                    'action': 'create_suite',
                    'args': {
                        'name': name,
                        'testcases': $scope.testsuiteList
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create suite success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                    } else {

                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            function openDialog() {
                ngDialog.open({
                    template: 'views/modal/suiteName.html',
                    className: 'ngdialog-theme-default',
                    scope: $scope,
                    width: 314,
                    showClose: true,
                    closeByDocument: false
                })
            }








        }
    ]);