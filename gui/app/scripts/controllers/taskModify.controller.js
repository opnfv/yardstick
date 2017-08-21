'use strict';

angular.module('yardStickGui2App')
    .controller('TaskModifyController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster) {


            init();
            $scope.blisterPackTemplates = [{ id: 1, name: "Test Case" }, { id: 2, name: "Test Suite" }]
            $scope.selectType = null;

            $scope.sourceShow = null;



            function init() {
                getDetailTaskForList();
                getEnvironmentList();
                $scope.triggerContent = triggerContent;
                $scope.constructTestSuit = constructTestSuit;
                $scope.constructTestCase = constructTestCase;
                $scope.getTestDeatil = getTestDeatil;
                $scope.confirmToServer = confirmToServer;
                $scope.addEnvToTask = addEnvToTask;
            }

            function getDetailTaskForList() {
                mainFactory.getTaskDetail().get({
                    'taskId': $stateParams.taskId
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

                        $scope.taskDetailData = response.result.task;
                        $scope.selectEnv = $scope.taskDetailData.environment_id;

                        if ($scope.taskDetailData.environment_id != null) {
                            getItemIdDetail($scope.taskDetailData.environment_id);
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

            function getItemIdDetail(id) {
                mainFactory.ItemDetail().get({
                    'envId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.envName = response.result.environment.name;
                        // $scope.selectEnv = $scope.envName;
                    } else {
                        alert('Something Wrong!');
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

            //getopenRcid
            function getOpenrcDetail(openrcId) {
                mainFactory.getEnvironmentDetail().get({
                    'openrc_id': openrcId
                }).$promise.then(function(response) {
                    $scope.openrcInfo = response.result;
                    // buildToEnvInfo($scope.openrcInfo.openrc)
                }, function(response) {

                })
            }


            //getImgDetail
            function getImageDetail(id) {
                mainFactory.ImageDetail().get({
                    'image_id': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.imageDetail = response.result.image;

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

            //getPodDetail
            function getPodDetail(id) {
                mainFactory.podDeatil().get({
                    'podId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.podDetail = response.result.pod;
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
            //getContainerDetail
            function getContainerId(containerId) {
                mainFactory.containerDetail().get({
                    'containerId': containerId
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.container = response.result.container;
                        $scope.displayContainerDetail.push($scope.container);

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


            function triggerContent(name) {
                $scope.selectCase = null;
                $scope.displayTable = true;

                $scope.selectType = name;
                if (name.name == 'Test Case') {
                    $scope.taskDetailData.suite = false;
                    getTestcaseList();
                } else if (name.name == 'Test Suite') {
                    $scope.taskDetailData.suite = true;
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


            function constructTestSuit(id, name) {

                $scope.envName = name;
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


            function getTestDeatil() {


                if ($scope.selectType.name == 'Test Case') {
                    getTestcaseDetail();
                } else {
                    getSuiteDetail();
                }

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



            function addCasetoTask(content) {
                mainFactory.taskAddEnv().put({
                    'taskId': $stateParams.taskId,
                    'action': 'add_case',
                    'args': {
                        'task_id': $stateParams.taskId,
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
                            body: '',
                            timeout: 3000
                        });
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'create task wrong',
                        body: '',
                        timeout: 3000
                    });
                })
            }

            function addSuitetoTask(content) {
                mainFactory.taskAddEnv().put({
                    'taskId': $stateParams.taskId,
                    'action': 'add_suite',
                    'args': {
                        'task_id': $stateParams.taskId,
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
            $scope.changeStatussourceTrue = function changeStatussourceTrue() {
                $scope.selectCase = null;
                $scope.sourceShow = true;
            }

            $scope.changeStatussourceFalse = function changeStatussourceFalse() {
                $scope.sourceShow = false;
            }

            function confirmToServer(content1, content2) {

                var content;
                if ($scope.sourceShow == false) {
                    content = content2;
                    $scope.selectCase = $scope.taskDetailData.case_name;
                } else if ($scope.sourceShow == true) {
                    content = content1;
                }
                if ($scope.selectCase == 'Test Case' || $scope.taskDetailData.suite == false) {

                    addCasetoTask(content);
                } else {
                    addSuitetoTask(content);
                }
            }


            function addEnvToTask() {

                mainFactory.taskAddEnv().put({
                    'taskId': $stateParams.taskId,
                    'action': 'add_environment',
                    'args': {
                        'task_id': $stateParams.taskId,
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

            $scope.goBack = function goBack() {
                window.history.back();
            }

            $scope.runAtask = function runAtask() {
                mainFactory.taskAddEnv().put({
                    'taskId': $stateParams.taskId,
                    'action': 'run',
                    'args': {
                        'task_id': $stateParams.taskId
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'run a task success',
                            body: 'go to task list page...',
                            timeout: 3000
                        });
                        setTimeout(function() {
                            window.history.back();
                        }, 2000);



                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'fail',
                            body: response.error_msg,
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
