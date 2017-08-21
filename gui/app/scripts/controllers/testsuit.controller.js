'use strict';

angular.module('yardStickGui2App')
    .controller('SuiteListController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog', '$loading',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog, $loading) {


            init();


            function init() {
                $scope.testsuitlist = [];
                getsuiteList();
                $scope.gotoDetail = gotoDetail;
                $scope.gotoCreateSuite = gotoCreateSuite;


            }

            function getsuiteList() {
                $loading.start('key');
                mainFactory.suiteList().get({

                }).$promise.then(function(response) {
                    $loading.finish('key');
                    if (response.status == 1) {
                        $scope.testsuitlist = response.result.testsuites;

                    }
                }, function(error) {
                    $loading.finish('key');
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            function gotoDetail(name) {
                var temp = name.split('.')[0];

                $state.go('app.suitedetail', { name: temp })

            }

            function gotoCreateSuite() {
                $state.go('app.suitcreate');
            }

            $scope.goBack = function goBack() {
                $state.go('app.projectList');
            }


            $scope.openDeleteEnv = function openDeleteEnv(id, name) {
                $scope.deleteName = name;
                $scope.deleteId = id.split('.')[0];
                ngDialog.open({
                    template: 'views/modal/deleteConfirm.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 500,
                    showClose: true,
                    closeByDocument: false
                })

            }

            $scope.deleteSuite = function deleteSuite() {
                mainFactory.deleteTestSuite().delete({ 'suite_name': $scope.deleteId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete Test Suite success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getTestcaseList();
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'Wrong',
                            body: response.result,
                            timeout: 3000
                        });
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


















        }
    ]);