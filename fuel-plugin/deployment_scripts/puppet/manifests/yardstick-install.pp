$fuel_settings = parseyaml(file('/etc/astute.yaml'))
$master_ip = $::fuel_settings['master_ip']

$access_hash    = hiera_hash('access', {})
$admin_tenant   = $access_hash['tenant']
$admin_user     = $access_hash['user']
$admin_password = $access_hash['password']
$region         = hiera('region', 'RegionOne')

$service_endpoint       = hiera('service_endpoint', $management_vip)
$ssl_hash               = hiera_hash('use_ssl', {})
$internal_auth_protocol = get_ssl_property($ssl_hash, {}, 'keystone', 'internal', 'protocol', 'http')
$internal_auth_address  = get_ssl_property($ssl_hash, {}, 'keystone', 'internal', 'hostname', [$service_endpoint])
$identity_uri           = "${internal_auth_protocol}://${internal_auth_address}:5000"
$auth_url               = "${identity_uri}/${auth_api_version}"

exec { "install yardstick":
    command => "curl http://${master_ip}:8080/plugins/fuel-plugin-yardstick-0.9/deployment_scripts/install.sh | bash -s ${master_ip}",
    path   => "/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin";
}

osnailyfacter::credentials_file { '/opt/yardstick/openrc':
  admin_user          => $admin_user,
  admin_password      => $admin_password,
  admin_tenant        => $admin_tenant,
  region_name         => $region,
  auth_url            => $auth_url,
}

exec { "run yardstick":
    command => "echo hello",
    path   => "/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin";
}
