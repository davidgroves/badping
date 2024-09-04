# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Define the Debian 12 base box
  config.vm.box = "generic/debian12"

  # Base box configuration
  config.vm.synced_folder ".", "/vagrant", type: "nfs", nfs_version: "4"

  # Libvirt configuration
  config.vm.provider "libvirt" do |libvirt|
    libvirt.cpus = 1
    libvirt.memory = 512
    libvirt.nic_model_type = "e1000"
  end
  
  # Provision script to install stuff.
  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y nfs-common tcpdump python3 python-is-python3 python3-pip python3-virtualenv python-is-python3 ethtool linux-source-6.1
    sudo pip3 install netifaces --break-system-packages
    sudo ethtool -K eth1 rx-fcs off
    sudo ethtool -K eth1 rx-all on
    sudo ethtool -K eth1 rx-checksumming off
    sudo ethtool -K eth1 tx-checksumming off
    cd /usr/src/
    sudo xz --decompress linux-source-6.1.tar.xz
    sudo tar xf linux-source-6.1.tar


  SHELL

  # Box A configuration
  config.vm.define "boxA" do |boxA|
    boxA.vm.hostname = "boxA"
    boxA.vm.network "private_network", ip: "192.168.50.10", netmask: "255.255.255.0", mac: "00:00:00:AA:AA:AA"
  end

  # Box B configuration
  config.vm.define "boxB" do |boxB|
    boxB.vm.hostname = "boxB"
    boxB.vm.network "private_network", ip: "192.168.50.11", netmask: "255.255.255.0", mac: "00:00:00:BB:BB:BB"
  end
end