'use strict';

angular.module('yardStickGui2App')
    .controller('suiteDetailController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster) {


            init();


            function init() {

                getSuiteDetail();

            }

            function getSuiteDetail() {
                mainFactory.suiteDetail().get({
                    'suiteName': $stateParams.name

                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.suiteinfo = response.result.testsuite;

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
            $scope.goBack = function goBack() {
                window.history.back();
            }









        }
    ]);
