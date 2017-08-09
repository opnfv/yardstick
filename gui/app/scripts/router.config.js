'use strict';

angular.module('yardStickGui2App')
    .run(
        ['$rootScope', '$state', '$stateParams',
            function($rootScope, $state, $stateParams) {
                $rootScope.$state = $state;
                $rootScope.$stateParams = $stateParams;

            }
        ]
    )
    .config(['$stateProvider', '$urlRouterProvider', '$locationProvider',
        function($stateProvider, $urlRouterProvider, $locationProvider) {
            $urlRouterProvider
                .otherwise('main/environment');




            $stateProvider

                .state('app2', {
                    url: "/main",
                    controller: 'ContentController',
                    templateUrl: "views/main2.html",
                    ncyBreadcrumb: {
                        label: 'Main'
                    }
                })
                .state('app', {
                    url: "/main",
                    controller: 'ContentController',
                    templateUrl: "views/main.html",
                    ncyBreadcrumb: {
                        label: 'Main'
                    }
                })

            .state('app2.environment', {
                    url: '/environment',
                    templateUrl: 'views/environmentList.html',
                    controller: 'MainCtrl',
                    ncyBreadcrumb: {
                        label: 'Environment'
                    }
                })
                .state('app2.testcase', {
                    url: '/testcase',
                    templateUrl: 'views/testcaselist.html',
                    controller: 'TestcaseController',
                    ncyBreadcrumb: {
                        label: 'Test Case'
                    }
                })
                .state('app2.testsuite', {
                    url: '/suite',
                    templateUrl: 'views/suite.html',
                    controller: 'SuiteListController',
                    ncyBreadcrumb: {
                        label: 'Test Suite'
                    }
                })
                .state('app2.suitcreate', {
                    url: '/suitcreate',
                    templateUrl: 'views/testcasechoose.html',
                    controller: 'suitcreateController',
                    ncyBreadcrumb: {
                        label: 'Suite Create'
                    }
                })
                .state('app2.testcasedetail', {
                    url: '/testdetail/:name',
                    templateUrl: 'views/testcasedetail.html',
                    controller: 'testcaseDetailController',
                    ncyBreadcrumb: {
                        label: 'Test Case Detail'
                    },
                    params: { name: null }
                })
                .state('app2.suitedetail', {
                    url: '/suitedetail/:name',
                    templateUrl: 'views/suitedetail.html',
                    controller: 'suiteDetailController',
                    ncyBreadcrumb: {
                        label: 'Suite Detail'
                    },
                    params: { name: null }
                })
                .state('app.environmentDetail', {
                    url: '/envDetail/:uuid',
                    templateUrl: 'views/environmentDetail.html',
                    controller: 'DetailController',
                    params: { uuid: null, ifNew: null },
                    ncyBreadcrumb: {
                        label: 'Environment Detail'
                    }
                })
                .state('app.uploadImage', {
                    url: '/envimageDetail/:uuid',
                    templateUrl: 'views/uploadImage.html',
                    controller: 'ImageController',
                    params: { uuid: null },
                    ncyBreadcrumb: {
                        label: 'Upload Image'
                    }

                })
                .state('app.podUpload', {
                    url: '/envpodupload/:uuid',
                    templateUrl: 'views/podupload.html',
                    controller: 'PodController',
                    params: { uuid: null },
                    ncyBreadcrumb: {
                        label: 'Pod Upload'
                    }
                })
                .state('app.container', {
                    url: '/envcontainer/:uuid',
                    templateUrl: 'views/container.html',
                    controller: 'ContainerController',
                    params: { uuid: null },
                    ncyBreadcrumb: {
                        label: 'Container Manage'
                    }
                })
                .state('app2.projectList', {
                    url: '/project',
                    templateUrl: 'views/projectList.html',
                    controller: 'ProjectController',
                    ncyBreadcrumb: {
                        label: 'Project'
                    }

                })
                .state('app2.tasklist', {
                    url: '/task/:taskId',
                    templateUrl: 'views/taskList.html',
                    controller: 'TaskController',
                    params: { taskId: null },
                    ncyBreadcrumb: {
                        label: 'Task'
                    }

                })
                .state('app2.taskLog', {
                    url: '/task/:taskId/log',
                    templateUrl: 'views/taskLog.html',
                    controller: 'TaskLogController',
                    params: { taskId: null },
                    ncyBreadcrumb: {
                        label: 'TaskLog'
                    }

                })
                .state('app2.report', {
                    url: '/report/:taskId',
                    templateUrl: 'views/report.html',
                    controller: 'ReportController',
                    params: { taskId: null },
                    ncyBreadcrumb: {
                        label: 'Report'
                    }

                })
                .state('app2.projectdetail', {
                    url: '/projectdetail/:projectId',
                    templateUrl: 'views/projectdetail.html',
                    controller: 'ProjectDetailController',
                    params: { projectId: null },
                    ncyBreadcrumb: {
                        label: 'Project Detail'
                    }

                })
                .state('app2.taskModify', {
                    url: '/taskModify/:taskId',
                    templateUrl: 'views/taskmodify.html',
                    controller: 'TaskModifyController',
                    params: { taskId: null },
                    ncyBreadcrumb: {
                        label: 'Modify Task'
                    }


                })





        }
    ])
    .run();
