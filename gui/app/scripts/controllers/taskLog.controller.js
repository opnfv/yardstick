'use strict';

angular.module('yardStickGui2App').controller('TaskLogController', ['$scope', '$stateParams', '$http', '$interval', 'mainFactory', function ($scope, $stateParams, $http, $interval, mainFactory) {
        $scope.logLines = [];
        $scope.getLog = getLog;
        $scope.taskId = $stateParams.taskId;
        $scope.taskStatus = 0;
        $scope.index = 0;

        $scope.goBack = function goBack() {
            window.history.back();
        }

        function getLog(){

            function get_data(){
                mainFactory.getTaskLog().get({'taskId': $scope.taskId, 'index': $scope.index}).$promise.then(function(data){
                    angular.forEach(data.result.data, function(ele){
                        $scope.logLines.push(ele);
                        $scope.index = data.result.index;
                    });

                    if(data.status == 1){
                        $interval.cancel($scope.intervalTask);
                        $scope.taskStatus = 1;
                    }
                });
            }

            $scope.intervalTask = $interval(get_data, 2000);
        }

        getLog();
}]);
