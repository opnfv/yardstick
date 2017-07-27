'use strict';

angular.module('yardStickGui2App')
    .controller('testcaseDetailController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster) {


            init();


            function init() {

                getTestcaseDetail();


            }

            function getTestcaseDetail() {
                mainFactory.getTestcaseDetail().get({
                    'testcasename': $stateParams.name

                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.testcaseInfo = response.result.testcase;

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