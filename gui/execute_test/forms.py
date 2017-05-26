from django import forms


class RegressionForm(forms.Form):
    regression_type = forms.ChoiceField(
        choices=(('functional', 'Functional'),
                ('performance', 'Performance')),)
    deployment_type = forms.ChoiceField(
        choices=(('baremetal', 'Bare Metal'),
                ('sriov', 'SRIOV'),
                ('ovs', 'OVS')),)


class RegressionPriorityForm(forms.Form):
    priority = forms.ChoiceField(
        choices=((0, 0), (1, 1), (2, 2), (3, 3)))


class VNFConfigForm(forms.Form):
    lb_count = forms.IntegerField(
        label="LB Count",
        min_value=1,
        max_value=6)
    worker_threads = forms.IntegerField(
        min_value=1,
        max_value=8)
    worker_configuration = forms.ChoiceField(
        choices=(('1c/1t', '1C/1T'),
                ('1c/2t', '1C/2T')),)
    lb_config = forms.ChoiceField(
        label='LB Configuration',
        choices=(('SW', 'Software Load Balancer'),
                ('HW', 'Hardware Load Balancer')),)
