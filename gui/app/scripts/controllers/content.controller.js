'use strict';

angular.module('yardStickGui2App')
    .controller('ContentController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', '$localStorage',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, $localStorage) {




            init();
            $scope.showEnvironment = false;
            $scope.counldGoDetail = false;
            $scope.activeStatus = 0;

            $scope.$watch(function() {
                return location.hash
            }, function(newvalue, oldvalue) {
                if (location.hash.indexOf('project') > -1) {
                    $scope.projectShow = true;
                    $scope.taskShow = false;
                    $scope.reportShow = false;
                } else if (location.hash.indexOf('task') > -1) {
                    $scope.taskShow = true;
                    $scope.projectShow = true;
                } else if (location.hash.indexOf('report') > -1) {
                    $scope.reportShow = true;
                    $scope.taskShow = true;
                    $scope.projectShow = true;
                }

            })


            function init() {


                $scope.showEnvironments = showEnvironments;
                $scope.showSteps = $location.path().indexOf('project');
                $scope.test = test;
                $scope.gotoUploadPage = gotoUploadPage;
                $scope.gotoOpenrcPage = gotoOpenrcPage;
                $scope.gotoPodPage = gotoPodPage;
                $scope.gotoContainerPage = gotoContainerPage;
                $scope.gotoTestcase = gotoTestcase;
                $scope.gotoEnviron = gotoEnviron;
                $scope.gotoSuite = gotoSuite;
                $scope.gotoProject = gotoProject;
                $scope.gotoTask = gotoTask;
                $scope.gotoReport = gotoReport;
                $scope.stepsStatus = $localStorage.stepsStatus;
                $scope.goBack = goBack;


            }



            function showEnvironments() {
                $scope.showEnvironment = true;
            }

            function test() {
                alert('test');
            }

            function gotoOpenrcPage() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.environmentDetail', { uuid: $scope.uuid })
            }

            function gotoUploadPage() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.uploadImage', { uuid: $scope.uuid });
            }

            function gotoPodPage() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.podUpload', { uuid: $scope.uuid });
            }

            function gotoContainerPage() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.container', { uuid: $scope.uuid });
            }

            function gotoTestcase() {
                $state.go('app2.testcase');
            }

            function gotoEnviron() {
                if ($location.path().indexOf('env') > -1 || $location.path().indexOf('environment') > -1) {
                    $scope.counldGoDetail = true;
                }
                $state.go('app2.environment');
            }

            function gotoSuite() {
                $state.go('app2.testsuite');
            }

            function gotoProject() {
                $state.go('app2.projectList');
            }

            function gotoTask() {
                $state.go('app2.tasklist');
            }

            function gotoReport() {
                $state.go('app2.report');
            }

            function goBack() {
                if ($location.path().indexOf('main/environment')) {
                    return;
                } else if ($location.path().indexOf('main/envDetail/') || $location.path().indexOf('main/imageDetail/') ||
                    $location.path().indexOf('main/podupload/') || $location.path().indexOf('main/container/')) {
                    $state.go('app2.environment');
                    return;
                } else {
                    window.history.back();
                }

            }






        }
    ]);