'use strict';

angular.module('yardStickGui2App')
    .controller('ProjectDetailController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog', '$localStorage', '$loading', '$interval',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog, $localStorage, $loading, $interval) {


            init();
            // $scope.taskListDisplay = [];
            $scope.blisterPackTemplates = [{ id: 1, name: "Test Case" }, { id: 2, name: "Test Suite" }]
            $scope.selectType = null;
            $scope.ifHasEnv = false;
            $scope.ifHasCase = false;
            $scope.ifHasSuite = false;
            $scope.$on('$destroy', function() {
                $interval.cancel($scope.intervalCount)
            });
            $scope.finalTaskListDisplay = [];


            function init() {


                getProjectDetail();

                $scope.openCreate = openCreate;
                $scope.createTask = createTask;
                $scope.constructTestSuit = constructTestSuit;
                $scope.addEnvToTask = addEnvToTask;
                $scope.triggerContent = triggerContent;
                $scope.constructTestCase = constructTestCase;
                $scope.getTestDeatil = getTestDeatil;
                $scope.confirmAddCaseOrSuite = confirmAddCaseOrSuite;
                $scope.runAtask = runAtask;
                $scope.gotoDetail = gotoDetail;
                $scope.gotoReport = gotoReport;
                $scope.gotoModify = gotoModify;
                $scope.goBack = goBack;
                $scope.goToExternal = goToExternal;


            }

            function getProjectDetail() {
                if ($scope.intervalCount != undefined) {
                    $interval.cancel($scope.intervalCount);
                }
                $loading.start('key');
                $scope.taskListDisplay = [];
                $scope.finalTaskListDisplay = [];
                mainFactory.getProjectDetail().get({
                    project_id: $stateParams.projectId
                }).$promise.then(function(response) {
                    $loading.finish('key');
                    if (response.status == 1) {

                        $scope.projectData = response.result.project;
                        if ($scope.projectData.tasks.length != 0) {


                            for (var i = 0; i < $scope.projectData.tasks.length; i++) {
                                getDetailTaskForList($scope.projectData.tasks[i]);
                            }
                            $scope.intervalCount = $interval(function() {
                                getDetailForEachTask();
                            }, 10000);
                        } else {

                            if ($scope.intervalCount != undefined) {
                                $interval.cancel($scope.intervalCount);
                            }
                        }
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

            // function getProjectDetailSimple() {
            //     getDetailForEachTask();
            // }

            function openCreate() {
                $scope.newUUID = null;
                $scope.displayEnvName = null;
                $scope.selectEnv = null;
                $scope.selectCase = null;
                $scope.selectType = null;
                $scope.contentInfo = null;
                $scope.ifHasEnv = false;
                $scope.ifHasCase = false;
                $scope.ifHasSuite = false;

                // getEnvironmentList();
                $scope.selectEnv = null;
                ngDialog.open({
                    template: 'views/modal/taskCreate.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 800,
                    showClose: true,
                    closeByDocument: false,
                    preCloseCallback: function(value) {
                        getProjectDetail();
                    },
                })
            }

            function createTask(name) {
                mainFactory.createTask().post({
                    'action': 'create_task',
                    'args': {
                        'name': name,
                        'project_id': $stateParams.projectId
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create task success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.newUUID = response.result.uuid;
                        getEnvironmentList();

                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'create task wrong',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                    }



                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'create task wrong',
                        body: 'you can go next step',
                        timeout: 3000
                    });
                })
            }

            function getDetailTaskForList(id) {

                mainFactory.getTaskDetail().get({
                    'taskId': id
                }).$promise.then(function(response) {

                    if (response.status == 1) {
                        if (response.result.task.status == -1) {
                            response.result.task['stausWidth'] = '5%';
                        } else if (response.result.task.status == 0) {
                            response.result.task['stausWidth'] = '50%';
                        } else if (response.result.task.status == 1) {
                            response.result.task['stausWidth'] = '100%';
                        } else if (response.result.task.status == 2) {
                            response.result.task['stausWidth'] = 'red';
                        }
                        $scope.taskListDisplay.push(response.result.task);
                        console.log($scope.taskListDisplay);

                        $scope.finalTaskListDisplay = $scope.taskListDisplay;

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

            function getDetailTaskForListSimple(id, index) {

                mainFactory.getTaskDetail().get({
                    'taskId': id
                }).$promise.then(function(response) {

                    if (response.status == 1) {
                        if (response.result.task.status == -1) {

                            $scope.finalTaskListDisplay[index].stausWidth = '5%';
                            $scope.finalTaskListDisplay[index].status = response.result.task.status;
                        } else if (response.result.task.status == 0) {

                            $scope.finalTaskListDisplay[index].stausWidth = '50%';
                            $scope.finalTaskListDisplay[index].status = response.result.task.status;
                        } else if (response.result.task.status == 1) {

                            $scope.finalTaskListDisplay[index].stausWidth = '100%';
                            $scope.finalTaskListDisplay[index].status = response.result.task.status;
                        } else if (response.result.task.status == 2) {

                            $scope.finalTaskListDisplay[index].stausWidth = 'red';
                            $scope.finalTaskListDisplay[index].status = response.result.task.status;
                        }


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

            function getDetailForEachTask() {
                for (var i = 0; i < $scope.finalTaskListDisplay.length; i++) {
                    if ($scope.finalTaskListDisplay[i].status != 1 && $scope.finalTaskListDisplay[i].status != -1) {
                        getDetailTaskForListSimple($scope.finalTaskListDisplay[i].uuid, i);
                    }
                }
            }

            function getEnvironmentList() {
                mainFactory.getEnvironmentList().get().$promise.then(function(response) {
                    $scope.environmentList = response.result.environments;
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });

                })
            }

            function constructTestSuit(id, name) {
                $scope.displayEnvName = name;
                $scope.selectEnv = id;

            }

            function constructTestCase(name) {

                $scope.selectCase = name;
                if ($scope.selectType.name == 'Test Case') {
                    getCaseInfo();
                } else {
                    getSuiteInfo();
                }

            }




            function addEnvToTask() {
                mainFactory.taskAddEnv().put({
                    'taskId': $scope.newUUID,
                    'action': 'add_environment',
                    'args': {
                        'task_id': $scope.newUUID,
                        'environment_id': $scope.selectEnv
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'add environment success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.ifHasEnv = true;


                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'create task wrong',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                    }



                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'create task wrong',
                        body: 'you can go next step',
                        timeout: 3000
                    });
                })
            }

            function triggerContent(name) {
                $scope.selectCase = null;
                $scope.displayTable = true;

                $scope.selectType = name;
                if (name.name == 'Test Case') {
                    getTestcaseList();
                } else if (name.name == 'Test Suite') {
                    getsuiteList();
                }
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

            function getsuiteList() {
                mainFactory.suiteList().get({

                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.testsuitlist = response.result.testsuites;

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

            function getTestDeatil() {


                if ($scope.selectType.name == 'Test Case') {
                    getTestcaseDetail();
                } else {
                    getSuiteDetail();
                }

            }

            function getCaseInfo() {



                mainFactory.getTestcaseDetail().get({
                    'testcasename': $scope.selectCase

                }).$promise.then(function(response) {
                    if (response.status == 1) {

                        $scope.contentInfo = response.result.testcase;

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

            function getSuiteInfo() {
                mainFactory.suiteDetail().get({
                    'suiteName': $scope.selectCase.split('.')[0]

                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.contentInfo = response.result.testsuite;

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


            function getSuiteDetail() {
                mainFactory.suiteDetail().get({
                    'suiteName': $scope.selectCase.split('.')[0]

                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.displayTable = false;
                        $scope.contentInfo = response.result.testsuite;

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


            function getTestcaseDetail() {
                mainFactory.getTestcaseDetail().get({
                    'testcasename': $scope.selectCase

                }).$promise.then(function(response) {
                    if (response.status == 1) {

                        $scope.displayTable = false;
                        $scope.contentInfo = response.result.testcase;
                        $scope.optionalParams = response.result.args;

                    }
                }, function(error) {
                    mainFactory.errorHandler2(error);
                })
            }


            function addParamsToTask(){
                var params = {}
                angular.forEach($scope.optionalParams, function(value, name){
                    if(value.value){
                        params[name] = value.value;
                    }
                });

                mainFactory.taskAddParams().put({
                    'taskId': $scope.newUUID,
                    'action': 'add_params',
                    'args': {
                        'params': params
                    }
                }).$promise.then(function(resp) {
                    if (resp.status == 1) {
                    } else {
                        mainFactory.errorHandler1(resp);
                    }
                }, function(error) {
                    mainFactory.errorHandler2(error);
                })
            }

            function addCasetoTask(content) {
                mainFactory.taskAddEnv().put({
                    'taskId': $scope.newUUID,
                    'action': 'add_case',
                    'args': {
                        'task_id': $scope.newUUID,
                        'case_name': $scope.selectCase,
                        'case_content': content
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'add test case success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.ifHasCase = true;


                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'create task wrong',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'create task wrong',
                        body: 'you can go next step',
                        timeout: 3000
                    });
                })
            }

            function addSuitetoTask(content) {
                mainFactory.taskAddEnv().put({
                    'taskId': $scope.newUUID,
                    'action': 'add_suite',
                    'args': {
                        'task_id': $scope.newUUID,
                        'suite_name': $scope.selectCase.split('.')[0],
                        'suite_content': content
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'add test suite success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.ifHasSuite = true;


                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'create task wrong',
                            body: 'wrong',
                            timeout: 3000
                        });
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'create task wrong',
                        body: 'something wrong',
                        timeout: 3000
                    });
                })
            }

            function confirmAddCaseOrSuite(content) {
                if ($scope.selectType.name == "Test Case") {
                    addCasetoTask(content);
                    addParamsToTask();
                } else {
                    addSuitetoTask(content);
                }
            }

            function runAtask(id) {
                mainFactory.taskAddEnv().put({
                    'taskId': id,
                    'action': 'run',
                    'args': {
                        'task_id': id
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'run a task success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        // getProjectDetail();
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

            $scope.runAtaskForTable = function runAtaskForTable(id) {
                mainFactory.taskAddEnv().put({
                    'taskId': id,
                    'action': 'run',
                    'args': {
                        'task_id': id
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        // toaster.pop({
                        //     type: 'success',
                        //     title: 'run a task success',
                        //     body: 'you can go next step',
                        //     timeout: 3000
                        // });
                        // ngDialog.close();
                        getProjectDetail();
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'fail',
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

            function gotoDetail(id) {


                $state.go('app.tasklist', { taskId: id });

            }

            function gotoReport(id) {
                $state.go('app.report', { taskId: id });
            }

            function gotoModify(id) {
                $state.go('app.taskModify', { taskId: id });
            }

            function goBack() {
                window.history.back();
            }

            function goToExternal() {
                window.open(External_URL, '_blank');
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

            $scope.deleteTask = function deleteTask() {
                mainFactory.deleteTask().delete({ 'task_id': $scope.deleteId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete Task success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getProjectDetail();
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

            $scope.gotoLog = function gotoLog(task_id) {
                $state.go('app.taskLog', { taskId: task_id });
            }
        }
    ]);
