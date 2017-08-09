'use strict';

angular.module('yardStickGui2App')
    .controller('ProjectController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog', '$loading',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog, $loading) {


            init();


            function init() {


                getProjectList();
                $scope.openCreateProject = openCreateProject;
                $scope.createName = createName;
                $scope.gotoDetail = gotoDetail;


            }

            function getProjectList() {
                $loading.start('key');
                mainFactory.projectList().get({}).$promise.then(function(response) {
                    $loading.finish('key');
                    if (response.status == 1) {
                        $scope.projectListData = response.result.projects;


                    } else {

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

            function openCreateProject() {

                ngDialog.open({
                    template: 'views/modal/projectCreate.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 400,
                    showClose: true,
                    closeByDocument: false
                })
            }

            function createName(name) {

                mainFactory.createProjectName().post({
                    'action': 'create_project',
                    'args': {
                        'name': name,
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create project success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getProjectList();
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'failed',
                            body: 'create project failed',
                            timeout: 3000
                        });
                    }

                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'failed',
                        body: 'Something Wrong',
                        timeout: 3000
                    });
                })
            }

            function gotoDetail(id) {
                $state.go('app.projectdetail', { projectId: id })
            }


            $scope.openDeleteEnv = function openDeleteEnv(id, name) {
                $scope.deleteName = name;
                $scope.deleteId = id;
                ngDialog.open({
                    template: 'views/modal/deleteConfirm.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 500,
                    showClose: true,
                    closeByDocument: false
                })

            }

            $scope.deleteProject = function deleteProject() {
                mainFactory.deleteProject().delete({ 'project_id': $scope.deleteId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete Project success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getProjectList();
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
