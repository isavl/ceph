#
# spec file for package ceph
#
# Copyright (C) 2004-2019 The Ceph Project Developers. See COPYING file
# at the top-level directory of this distribution and at
# https://github.com/ceph/ceph/blob/master/COPYING
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon.
#
# This file is under the GNU Lesser General Public License, version 2.1
#
# Please submit bugfixes or comments via http://tracker.ceph.com/
#

#################################################################################
# conditional build section
#
# please read this for explanation of bcond syntax:
# https://rpm-software-management.github.io/rpm/manual/conditionalbuilds.html
#################################################################################
%bcond_with make_check
%bcond_with zbd
%bcond_with cmake_verbose_logging
%bcond_without ceph_test_package
%ifarch s390
%bcond_with tcmalloc
%else
%bcond_without tcmalloc
%endif
%bcond_without rbd_ssd_cache
%ifarch x86_64
%bcond_without rbd_rwl_cache
%else
%bcond_with rbd_rwl_cache
%endif
%if 0%{?fedora} || 0%{?rhel}
%if 0%{?rhel} < 9
%bcond_with system_pmdk
%else
%bcond_without system_pmdk
%endif
%bcond_without selinux
%if 0%{?rhel} >= 8
%bcond_with cephfs_java
%else
%bcond_without cephfs_java
%endif
%bcond_without amqp_endpoint
%bcond_without kafka_endpoint
%bcond_without lttng
%bcond_without libradosstriper
%bcond_without ocf
%global luarocks_package_name luarocks
%bcond_without lua_packages
%global _remote_tarball_prefix https://download.ceph.com/tarballs/
%endif
%if 0%{?suse_version}
%bcond_without system_pmdk
%bcond_with amqp_endpoint
%bcond_with cephfs_java
%bcond_with kafka_endpoint
%bcond_with libradosstriper
%ifarch x86_64 aarch64 ppc64le
%bcond_without lttng
%else
%bcond_with lttng
%endif
%bcond_with ocf
%bcond_with selinux
#Compat macro for _fillupdir macro introduced in Nov 2017
%if ! %{defined _fillupdir}
%global _fillupdir /var/adm/fillup-templates
%endif
#luarocks
%if 0%{?is_opensuse}
# openSUSE
%bcond_without lua_packages
%if 0%{?sle_version}
# openSUSE Leap
%global luarocks_package_name lua53-luarocks
%else
# openSUSE Tumbleweed
%global luarocks_package_name lua54-luarocks
%endif
%else
# SLE
%bcond_with lua_packages
%endif
%endif
%bcond_with seastar
%bcond_with jaeger
%if 0%{?fedora} || 0%{?suse_version} >= 1500
# distros that ship cmd2 and/or colorama
%bcond_without cephfs_shell
%else
# distros that do _not_ ship cmd2/colorama
%bcond_with cephfs_shell
%endif
%bcond_with system_arrow
%bcond_with system_utf8proc
%if 0%{?fedora} || 0%{?suse_version} || 0%{?rhel} >= 8
%global weak_deps 1
%endif
%if %{with selinux}
# get selinux policy version
# Force 0.0.0 policy version for centos builds to avoid repository sync issues between rhel and centos
%if 0%{?centos}
%global _selinux_policy_version 0.0.0
%else
%{!?_selinux_policy_version: %global _selinux_policy_version 0.0.0}
%endif
%endif

%{!?_udevrulesdir: %global _udevrulesdir /lib/udev/rules.d}
%{!?tmpfiles_create: %global tmpfiles_create systemd-tmpfiles --create}
%{!?python3_pkgversion: %global python3_pkgversion 3}
%{!?python3_version_nodots: %global python3_version_nodots 3}
%{!?python3_version: %global python3_version 3}

%if ! 0%{?suse_version}
# use multi-threaded xz compression: xz level 7 using ncpus threads
%global _source_payload w7T%{_smp_build_ncpus}.xzdio
%global _binary_payload w7T%{_smp_build_ncpus}.xzdio
%endif

%define smp_limit_mem_per_job() %( \
  kb_per_job=%1 \
  kb_total=$(head -3 /proc/meminfo | sed -n 's/MemAvailable:\\s*\\(.*\\) kB.*/\\1/p') \
  jobs=$(( $kb_total / $kb_per_job )) \
  [ $jobs -lt 1 ] && jobs=1 \
  echo $jobs )

%if 0%{?_smp_ncpus_max} == 0
%if 0%{?__isa_bits} == 32
# 32-bit builds can use 3G memory max, which is not enough even for -j2
%global _smp_ncpus_max 1
%else
# 3.0 GiB mem per job
# SUSE distros use limit_build in the place of smp_limit_mem_per_job, please
# be sure to update it (in the build section, below) as well when changing this
# number.
%global _smp_ncpus_max %{smp_limit_mem_per_job 3000000}
%endif
%endif

%if 0%{with seastar}
# disable -specs=/usr/lib/rpm/redhat/redhat-annobin-cc1, as gcc-toolset-{9,10}-annobin
# do not provide gcc-annobin.so anymore, despite that they provide annobin.so. but
# redhat-rpm-config still passes -fplugin=gcc-annobin to the compiler.
%undefine _annotated_build
%endif

#################################################################################
# main package definition
#################################################################################
Name:		ceph
Version:	17.2.2
Release:	0%{?dist}
%if 0%{?fedora} || 0%{?rhel}
Epoch:		2
%endif

# define _epoch_prefix macro which will expand to the empty string if epoch is
# undefined
%global _epoch_prefix %{?epoch:%{epoch}:}

Summary:	User space components of the Ceph file system
License:	LGPL-2.1 and LGPL-3.0 and CC-BY-SA-3.0 and GPL-2.0 and BSL-1.0 and BSD-3-Clause and MIT
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
URL:		http://ceph.com/
Source0:	%{?_remote_tarball_prefix}ceph-17.2.2.tar.bz2
%if 0%{?suse_version}
# _insert_obs_source_lines_here
ExclusiveArch:  x86_64 aarch64 ppc64le s390x
%endif
#################################################################################
# dependencies that apply across all distro families
#################################################################################
Requires:       ceph-osd = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mds = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mon = %{_epoch_prefix}%{version}-%{release}
Requires(post):	binutils
%if 0%{with cephfs_java}
BuildRequires:	java-devel
BuildRequires:	sharutils
%endif
%if 0%{with selinux}
BuildRequires:	checkpolicy
BuildRequires:	selinux-policy-devel
%endif
BuildRequires:	gperf
BuildRequires:  cmake > 3.5
BuildRequires:	fuse-devel
%if 0%{with seastar} && 0%{?rhel}
BuildRequires:	gcc-toolset-9-gcc-c++ >= 9.2.1-2.3
%else
BuildRequires:	gcc-c++
%endif
%if 0%{with tcmalloc}
# libprofiler did not build on ppc64le until 2.7.90
%if 0%{?fedora} || 0%{?rhel} >= 8
BuildRequires:	gperftools-devel >= 2.7.90
%endif
%if 0%{?rhel} && 0%{?rhel} < 8
BuildRequires:	gperftools-devel >= 2.6.1
%endif
%if 0%{?suse_version}
BuildRequires:	gperftools-devel >= 2.4
%endif
%endif
BuildRequires:	libaio-devel
BuildRequires:	libblkid-devel >= 2.17
BuildRequires:	cryptsetup-devel
BuildRequires:	libcurl-devel
BuildRequires:	libcap-ng-devel
BuildRequires:	fmt-devel >= 6.2.1
BuildRequires:	pkgconfig(libudev)
BuildRequires:	libnl3-devel
BuildRequires:	liboath-devel
BuildRequires:	libtool
BuildRequires:	libxml2-devel
BuildRequires:	make
BuildRequires:	ncurses-devel
BuildRequires:	libicu-devel
BuildRequires:	patch
BuildRequires:	perl
BuildRequires:	pkgconfig
BuildRequires:  procps
BuildRequires:	python%{python3_pkgversion}
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	python%{python3_pkgversion}-setuptools
BuildRequires:	python%{python3_pkgversion}-Cython
BuildRequires:	snappy-devel
BuildRequires:	sqlite-devel
BuildRequires:	sudo
BuildRequires:	pkgconfig(udev)
BuildRequires:	valgrind-devel
BuildRequires:	which
BuildRequires:	xfsprogs-devel
BuildRequires:	xmlstarlet
BuildRequires:	nasm
BuildRequires:	lua-devel
%if 0%{with seastar} || 0%{with jaeger}
BuildRequires:  yaml-cpp-devel >= 0.6
%endif
%if 0%{with amqp_endpoint}
BuildRequires:  librabbitmq-devel
%endif
%if 0%{with kafka_endpoint}
BuildRequires:  librdkafka-devel
%endif
%if 0%{with lua_packages}
BuildRequires:  %{luarocks_package_name}
%endif
%if 0%{with make_check}
BuildRequires:  hostname
BuildRequires:  jq
BuildRequires:	libuuid-devel
BuildRequires:	python%{python3_pkgversion}-bcrypt
BuildRequires:	python%{python3_pkgversion}-pecan
BuildRequires:	python%{python3_pkgversion}-requests
BuildRequires:	python%{python3_pkgversion}-dateutil
BuildRequires:	python%{python3_pkgversion}-coverage
BuildRequires:	python%{python3_pkgversion}-pyOpenSSL
BuildRequires:	socat
%endif
%if 0%{with zbd}
BuildRequires:  libzbd-devel
%endif
%if 0%{?suse_version}
BuildRequires:  libthrift-devel >= 0.13.0
%else
BuildRequires:  thrift-devel >= 0.13.0
%endif
BuildRequires:  re2-devel
%if 0%{with jaeger}
BuildRequires:  bison
BuildRequires:  flex
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  json-devel
%endif
%if 0%{?suse_version}
BuildRequires:  nlohmann_json-devel
%endif
BuildRequires:  libevent-devel
%endif
%if 0%{with system_pmdk}
BuildRequires:  libpmem-devel
BuildRequires:  libpmemobj-devel
%endif
%if 0%{with system_arrow}
BuildRequires:  arrow-devel
BuildRequires:  parquet-devel
%endif
%if 0%{with system_utf8proc}
BuildRequires:  utf8proc-devel
%endif
%if 0%{with seastar}
BuildRequires:  c-ares-devel
BuildRequires:  gnutls-devel
BuildRequires:  hwloc-devel
BuildRequires:  libpciaccess-devel
BuildRequires:  lksctp-tools-devel
BuildRequires:  ragel
BuildRequires:  systemtap-sdt-devel
%if 0%{?fedora}
BuildRequires:  libubsan
BuildRequires:  libasan
BuildRequires:  libatomic
%endif
%if 0%{?rhel}
BuildRequires:  gcc-toolset-9-annobin
BuildRequires:  gcc-toolset-9-libubsan-devel
BuildRequires:  gcc-toolset-9-libasan-devel
BuildRequires:  gcc-toolset-9-libatomic-devel
%endif
%endif
#################################################################################
# distro-conditional dependencies
#################################################################################
%if 0%{?suse_version}
BuildRequires:  pkgconfig(systemd)
BuildRequires:	systemd-rpm-macros
%{?systemd_requires}
PreReq:		%fillup_prereq
BuildRequires:	fdupes
BuildRequires:  memory-constraints
BuildRequires:	net-tools
BuildRequires:	libbz2-devel
BuildRequires:	mozilla-nss-devel
BuildRequires:	keyutils-devel
BuildRequires:  libopenssl-devel
BuildRequires:  ninja
BuildRequires:  openldap2-devel
#BuildRequires:  krb5
#BuildRequires:  krb5-devel
BuildRequires:  cunit-devel
BuildRequires:	python%{python3_pkgversion}-PrettyTable
BuildRequires:	python%{python3_pkgversion}-PyYAML
BuildRequires:	python%{python3_pkgversion}-Sphinx
BuildRequires:  rdma-core-devel
BuildRequires:	liblz4-devel >= 1.7
# for prometheus-alerts
BuildRequires:  golang-github-prometheus-prometheus
%endif
%if 0%{?fedora} || 0%{?rhel}
Requires:	systemd
BuildRequires:  boost-random
BuildRequires:	nss-devel
BuildRequires:	keyutils-libs-devel
BuildRequires:	libibverbs-devel
BuildRequires:  librdmacm-devel
BuildRequires:  ninja-build
BuildRequires:  openldap-devel
#BuildRequires:  krb5-devel
BuildRequires:  openssl-devel
BuildRequires:  CUnit-devel
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	python%{python3_pkgversion}-prettytable
BuildRequires:	python%{python3_pkgversion}-pyyaml
BuildRequires:	python%{python3_pkgversion}-sphinx
BuildRequires:	lz4-devel >= 1.7
%endif
# distro-conditional make check dependencies
%if 0%{with make_check}
BuildRequires:	golang
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:	golang-github-prometheus
BuildRequires:	libtool-ltdl-devel
BuildRequires:	xmlsec1
BuildRequires:	xmlsec1-devel
%ifarch x86_64
BuildRequires:	xmlsec1-nss
%endif
BuildRequires:	xmlsec1-openssl
BuildRequires:	xmlsec1-openssl-devel
BuildRequires:	python%{python3_pkgversion}-cherrypy
BuildRequires:	python%{python3_pkgversion}-jwt
BuildRequires:	python%{python3_pkgversion}-routes
BuildRequires:	python%{python3_pkgversion}-scipy
BuildRequires:	python%{python3_pkgversion}-werkzeug
BuildRequires:	python%{python3_pkgversion}-pyOpenSSL
%endif
%if 0%{?suse_version}
BuildRequires:	golang-github-prometheus-prometheus
BuildRequires:	libxmlsec1-1
BuildRequires:	libxmlsec1-nss1
BuildRequires:	libxmlsec1-openssl1
BuildRequires:	python%{python3_pkgversion}-CherryPy
BuildRequires:	python%{python3_pkgversion}-PyJWT
BuildRequires:	python%{python3_pkgversion}-Routes
BuildRequires:	python%{python3_pkgversion}-Werkzeug
BuildRequires:	python%{python3_pkgversion}-numpy-devel
BuildRequires:	xmlsec1-devel
BuildRequires:	xmlsec1-openssl-devel
%endif
%endif
# lttng and babeltrace for rbd-replay-prep
%if %{with lttng}
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:	lttng-ust-devel
BuildRequires:	libbabeltrace-devel
%endif
%if 0%{?suse_version}
BuildRequires:	lttng-ust-devel
BuildRequires:  babeltrace-devel
%endif
%endif
%if 0%{?suse_version}
BuildRequires:	libexpat-devel
%endif
%if 0%{?rhel} || 0%{?fedora}
BuildRequires:	expat-devel
%endif
#hardened-cc1
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  redhat-rpm-config
%endif
%if 0%{with seastar}
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  cryptopp-devel
BuildRequires:  numactl-devel
%endif
%if 0%{?suse_version}
BuildRequires:  libcryptopp-devel
BuildRequires:  libnuma-devel
%endif
%endif
%if 0%{?rhel} >= 8
BuildRequires:  /usr/bin/pathfix.py
%endif

%description
Ceph is a massively scalable, open-source, distributed storage system that runs
on commodity hardware and delivers object, block and file system storage.


#################################################################################
# subpackages
#################################################################################
%package base
Summary:       Ceph Base Package
%if 0%{?suse_version}
Group:         System/Filesystems
%endif
Provides:      ceph-test:/usr/bin/ceph-kvstore-tool
Requires:      ceph-common = %{_epoch_prefix}%{version}-%{release}
Requires:      librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:      librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:      libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:      librgw2 = %{_epoch_prefix}%{version}-%{release}
%if 0%{with selinux}
Requires:      ceph-selinux = %{_epoch_prefix}%{version}-%{release}
%endif
Requires:      findutils
Requires:      grep
Requires:      logrotate
Requires:      psmisc
Requires:      util-linux
Requires:      which
%if 0%{?rhel} && 0%{?rhel} < 8
# The following is necessary due to tracker 36508 and can be removed once the
# associated upstream bugs are resolved.
%if 0%{with tcmalloc}
Requires:      gperftools-libs >= 2.6.1
%endif
%endif
%if 0%{?weak_deps}
Recommends:    chrony
Recommends:    nvme-cli
%if 0%{?suse_version}
Requires:      smartmontools
%else
Recommends:    smartmontools
%endif
%endif
%description base
Base is the package that includes all the files shared amongst ceph servers

%package -n cephadm
Summary:        Utility to bootstrap Ceph clusters
BuildArch:      noarch
Requires:       lvm2
Requires:       python%{python3_pkgversion}
Requires:       openssh-server
Requires:       which
%if 0%{?weak_deps}
Recommends:     podman >= 2.0.2
%endif
%description -n cephadm
Utility to bootstrap a Ceph cluster and manage Ceph daemons deployed
with systemd and podman.

%package -n ceph-common
Summary:	Ceph Common
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rbd = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-cephfs = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rgw = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-ceph-argparse = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-ceph-common = %{_epoch_prefix}%{version}-%{release}
%if 0%{?fedora} || 0%{?rhel}
Requires:	python%{python3_pkgversion}-prettytable
%endif
%if 0%{?suse_version}
Requires:	python%{python3_pkgversion}-PrettyTable
%endif
%if 0%{with libradosstriper}
Requires:	libradosstriper1 = %{_epoch_prefix}%{version}-%{release}
%endif
%{?systemd_requires}
%if 0%{?suse_version}
Requires(pre):	pwdutils
%endif
%description -n ceph-common
Common utilities to mount and interact with a ceph storage cluster.
Comprised of files that are common to Ceph clients and servers.

%package mds
Summary:	Ceph Metadata Server Daemon
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
%description mds
ceph-mds is the metadata server daemon for the Ceph distributed file system.
One or more instances of ceph-mds collectively manage the file system
namespace, coordinating access to the shared OSD cluster.

%package mon
Summary:	Ceph Monitor Daemon
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Provides:	ceph-test:/usr/bin/ceph-monstore-tool
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
%description mon
ceph-mon is the cluster monitor daemon for the Ceph distributed file
system. One or more instances of ceph-mon form a Paxos part-time
parliament cluster that provides extremely reliable and durable storage
of cluster membership, configuration, and state.

%package mgr
Summary:        Ceph Manager Daemon
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mgr-modules-core = %{_epoch_prefix}%{version}-%{release}
Requires:	    libcephsqlite = %{_epoch_prefix}%{version}-%{release}
%if 0%{?weak_deps}
Recommends:	ceph-mgr-dashboard = %{_epoch_prefix}%{version}-%{release}
Recommends:	ceph-mgr-diskprediction-local = %{_epoch_prefix}%{version}-%{release}
Recommends:	ceph-mgr-k8sevents = %{_epoch_prefix}%{version}-%{release}
Recommends:	ceph-mgr-cephadm = %{_epoch_prefix}%{version}-%{release}
Recommends:	python%{python3_pkgversion}-influxdb
%endif
%description mgr
ceph-mgr enables python modules that provide services (such as the REST
module derived from Calamari) and expose CLI hooks.  ceph-mgr gathers
the cluster maps, the daemon metadata, and performance counters, and
exposes all these to the python modules.

%package mgr-dashboard
Summary:        Ceph Dashboard
BuildArch:      noarch
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-grafana-dashboards = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-prometheus-alerts = %{_epoch_prefix}%{version}-%{release}
%if 0%{?fedora} || 0%{?rhel}
Requires:       python%{python3_pkgversion}-cherrypy
Requires:       python%{python3_pkgversion}-jwt
Requires:       python%{python3_pkgversion}-routes
Requires:       python%{python3_pkgversion}-werkzeug
%if 0%{?weak_deps}
Recommends:     python%{python3_pkgversion}-saml
%endif
%endif
%if 0%{?suse_version}
Requires:       python%{python3_pkgversion}-CherryPy
Requires:       python%{python3_pkgversion}-PyJWT
Requires:       python%{python3_pkgversion}-Routes
Requires:       python%{python3_pkgversion}-Werkzeug
Recommends:     python%{python3_pkgversion}-python3-saml
%endif
%description mgr-dashboard
ceph-mgr-dashboard is a manager module, providing a web-based application
to monitor and manage many aspects of a Ceph cluster and related components.
See the Dashboard documentation at http://docs.ceph.com/ for details and a
detailed feature overview.

%package mgr-diskprediction-local
Summary:        Ceph Manager module for predicting disk failures
BuildArch:      noarch
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       python%{python3_pkgversion}-numpy
%if 0%{?fedora} || 0%{?suse_version}
Requires:       python%{python3_pkgversion}-scikit-learn
%endif
Requires:       python3-scipy
%description mgr-diskprediction-local
ceph-mgr-diskprediction-local is a ceph-mgr module that tries to predict
disk failures using local algorithms and machine-learning databases.

%package mgr-modules-core
Summary:        Ceph Manager modules which are always enabled
BuildArch:      noarch
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       python%{python3_pkgversion}-bcrypt
Requires:       python%{python3_pkgversion}-pecan
Requires:       python%{python3_pkgversion}-pyOpenSSL
Requires:       python%{python3_pkgversion}-requests
Requires:       python%{python3_pkgversion}-dateutil
%if 0%{?fedora} || 0%{?rhel} >= 8
Requires:       python%{python3_pkgversion}-cherrypy
Requires:       python%{python3_pkgversion}-pyyaml
Requires:       python%{python3_pkgversion}-werkzeug
%endif
%if 0%{?suse_version}
Requires:       python%{python3_pkgversion}-CherryPy
Requires:       python%{python3_pkgversion}-PyYAML
Requires:       python%{python3_pkgversion}-Werkzeug
%endif
%if 0%{?weak_deps}
Recommends:	ceph-mgr-rook = %{_epoch_prefix}%{version}-%{release}
%endif
%description mgr-modules-core
ceph-mgr-modules-core provides a set of modules which are always
enabled by ceph-mgr.

%package mgr-rook
BuildArch:      noarch
Summary:        Ceph Manager module for Rook-based orchestration
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       python%{python3_pkgversion}-kubernetes
Requires:       python%{python3_pkgversion}-jsonpatch
%description mgr-rook
ceph-mgr-rook is a ceph-mgr module for orchestration functions using
a Rook backend.

%package mgr-k8sevents
BuildArch:      noarch
Summary:        Ceph Manager module to orchestrate ceph-events to kubernetes' events API
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       python%{python3_pkgversion}-kubernetes
%description mgr-k8sevents
ceph-mgr-k8sevents is a ceph-mgr module that sends every ceph-events
to kubernetes' events API

%package mgr-cephadm
Summary:        Ceph Manager module for cephadm-based orchestration
BuildArch:	noarch
%if 0%{?suse_version}
Group:          System/Filesystems
%endif
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       python%{python3_pkgversion}-asyncssh
Requires:       python%{python3_pkgversion}-natsort
Requires:       cephadm = %{_epoch_prefix}%{version}-%{release}
%if 0%{?suse_version}
Requires:       openssh
Requires:       python%{python3_pkgversion}-CherryPy
Requires:       python%{python3_pkgversion}-Jinja2
%endif
%if 0%{?rhel} || 0%{?fedora}
Requires:       openssh-clients
Requires:       python%{python3_pkgversion}-cherrypy
Requires:       python%{python3_pkgversion}-jinja2
%endif
%description mgr-cephadm
ceph-mgr-cephadm is a ceph-mgr module for orchestration functions using
the integrated cephadm deployment tool management operations.

%package fuse
Summary:	Ceph fuse-based client
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:       fuse
Requires:	python%{python3_pkgversion}
%description fuse
FUSE based client for Ceph distributed network file system

%package -n cephfs-mirror
Summary:	Ceph daemon for mirroring CephFS snapshots
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
%description -n cephfs-mirror
Daemon for mirroring CephFS snapshots between Ceph clusters.

%package -n rbd-fuse
Summary:	Ceph fuse-based client
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
%description -n rbd-fuse
FUSE based client to map Ceph rbd images to files

%package -n rbd-mirror
Summary:	Ceph daemon for mirroring RBD images
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
%description -n rbd-mirror
Daemon for mirroring RBD images between Ceph clusters, streaming
changes asynchronously.

%package immutable-object-cache
Summary:	Ceph daemon for immutable object cache
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%description immutable-object-cache
Daemon for immutable object cache.

%package -n rbd-nbd
Summary:	Ceph RBD client base on NBD
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
%description -n rbd-nbd
NBD based client to map Ceph rbd images to local device

%package radosgw
Summary:	Rados REST gateway
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
%if 0%{with selinux}
Requires:	ceph-selinux = %{_epoch_prefix}%{version}-%{release}
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librgw2 = %{_epoch_prefix}%{version}-%{release}
%if 0%{?rhel} || 0%{?fedora}
Requires:	mailcap
%endif
%if 0%{?weak_deps}
Recommends:	gawk
%endif
%description radosgw
RADOS is a distributed object store used by the Ceph distributed
storage system.  This package provides a REST gateway to the
object store that aims to implement a superset of Amazon's S3
service as well as the OpenStack Object Storage ("Swift") API.

%package -n cephfs-top
Summary:    top(1) like utility for Ceph Filesystem
BuildArch:  noarch
Requires:   python%{python3_pkgversion}-rados
%description -n cephfs-top
This package provides a top(1) like utility to display Ceph Filesystem metrics
in realtime.

%if %{with ocf}
%package resource-agents
Summary:	OCF-compliant resource agents for Ceph daemons
BuildArch:	noarch
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}
Requires:	resource-agents
%description resource-agents
Resource agents for monitoring and managing Ceph daemons
under Open Cluster Framework (OCF) compliant resource
managers such as Pacemaker.
%endif

%package osd
Summary:	Ceph Object Storage Daemon
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Provides:	ceph-test:/usr/bin/ceph-osdomap-tool
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires:	sudo
Requires:	libstoragemgmt
%if 0%{?weak_deps}
Recommends:	ceph-volume = %{_epoch_prefix}%{version}-%{release}
%endif
%description osd
ceph-osd is the object storage daemon for the Ceph distributed file
system.  It is responsible for storing objects on a local file system
and providing access to them over the network.

%if 0%{with seastar}
%package crimson-osd
Summary:	Ceph Object Storage Daemon (crimson)
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-osd = %{_epoch_prefix}%{version}-%{release}
Requires:	binutils
%description crimson-osd
crimson-osd is the object storage daemon for the Ceph distributed file
system.  It is responsible for storing objects on a local file system
and providing access to them over the network.
%endif

%package volume
Summary: Ceph OSD deployment and inspection tool
BuildArch: noarch
%if 0%{?suse_version}
Group: System/Filesystems
%endif
Requires: ceph-osd = %{_epoch_prefix}%{version}-%{release}
Requires: cryptsetup
Requires: e2fsprogs
Requires: lvm2
Requires: parted
Requires: util-linux
Requires: xfsprogs
Requires: python%{python3_pkgversion}-setuptools
Requires: python%{python3_pkgversion}-ceph-common = %{_epoch_prefix}%{version}-%{release}
%description volume
This package contains a tool to deploy OSD with different devices like
lvm or physical disks, and trying to follow a predictable, and robust
way of preparing, activating, and starting the deployed OSD.

%package -n librados2
Summary:	RADOS distributed object store client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{_epoch_prefix}%{version}-%{release}
%endif
%description -n librados2
RADOS is a reliable, autonomic distributed object storage cluster
developed as part of the Ceph distributed storage system. This is a
shared library allowing applications to access the distributed object
store using a simple file-like interface.

%package -n librados-devel
Summary:	RADOS headers
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-devel < %{_epoch_prefix}%{version}-%{release}
Provides:	librados2-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	librados2-devel < %{_epoch_prefix}%{version}-%{release}
%description -n librados-devel
This package contains C libraries and headers needed to develop programs
that use RADOS object store.

%package -n libradospp-devel
Summary:	RADOS headers
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librados-devel = %{_epoch_prefix}%{version}-%{release}
%description -n libradospp-devel
This package contains C++ libraries and headers needed to develop programs
that use RADOS object store.

%package -n librgw2
Summary:	RADOS gateway client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%description -n librgw2
This package provides a library implementation of the RADOS gateway
(distributed object store with S3 and Swift personalities).

%package -n librgw-devel
Summary:	RADOS gateway client library
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	librados-devel = %{_epoch_prefix}%{version}-%{release}
Requires:	librgw2 = %{_epoch_prefix}%{version}-%{release}
Provides:	librgw2-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	librgw2-devel < %{_epoch_prefix}%{version}-%{release}
%description -n librgw-devel
This package contains libraries and headers needed to develop programs
that use RADOS gateway client library.

%package -n python%{python3_pkgversion}-rgw
Summary:	Python 3 libraries for the RADOS gateway
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	librgw2 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-rgw}
Provides:	python-rgw = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-rgw < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-rgw
This package contains Python 3 libraries for interacting with Ceph RADOS
gateway.

%package -n python%{python3_pkgversion}-rados
Summary:	Python 3 libraries for the RADOS object store
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	python%{python3_pkgversion}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-rados}
Provides:	python-rados = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-rados < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-rados
This package contains Python 3 libraries for interacting with Ceph RADOS
object store.

%package -n libcephsqlite
Summary:	SQLite3 VFS for Ceph
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%description -n libcephsqlite
A SQLite3 VFS for storing and manipulating databases stored on Ceph's RADOS
distributed object store.

%package -n libcephsqlite-devel
Summary:	SQLite3 VFS for Ceph headers
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	sqlite-devel
Requires:	libcephsqlite = %{_epoch_prefix}%{version}-%{release}
Requires:	librados-devel = %{_epoch_prefix}%{version}-%{release}
Requires:	libradospp-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-devel < %{_epoch_prefix}%{version}-%{release}
Provides:	libcephsqlite-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	libcephsqlite-devel < %{_epoch_prefix}%{version}-%{release}
%description -n libcephsqlite-devel
A SQLite3 VFS for storing and manipulating databases stored on Ceph's RADOS
distributed object store.

%if 0%{with libradosstriper}
%package -n libradosstriper1
Summary:	RADOS striping interface
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%description -n libradosstriper1
Striping interface built on top of the rados library, allowing
to stripe bigger objects onto several standard rados objects using
an interface very similar to the rados one.

%package -n libradosstriper-devel
Summary:	RADOS striping interface headers
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	libradosstriper1 = %{_epoch_prefix}%{version}-%{release}
Requires:	librados-devel = %{_epoch_prefix}%{version}-%{release}
Requires:	libradospp-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-devel < %{_epoch_prefix}%{version}-%{release}
Provides:	libradosstriper1-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	libradosstriper1-devel < %{_epoch_prefix}%{version}-%{release}
%description -n libradosstriper-devel
This package contains libraries and headers needed to develop programs
that use RADOS striping interface.
%endif

%package -n librbd1
Summary:	RADOS block device client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%if 0%{?suse_version}
Requires(post): coreutils
%endif
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{_epoch_prefix}%{version}-%{release}
%endif
%description -n librbd1
RBD is a block device striped across multiple distributed objects in
RADOS, a reliable, autonomic distributed object storage cluster
developed as part of the Ceph distributed storage system. This is a
shared library allowing applications to manage these block devices.

%package -n librbd-devel
Summary:	RADOS block device headers
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:	librados-devel = %{_epoch_prefix}%{version}-%{release}
Requires:	libradospp-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-devel < %{_epoch_prefix}%{version}-%{release}
Provides:	librbd1-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	librbd1-devel < %{_epoch_prefix}%{version}-%{release}
%description -n librbd-devel
This package contains libraries and headers needed to develop programs
that use RADOS block device.

%package -n python%{python3_pkgversion}-rbd
Summary:	Python 3 libraries for the RADOS block device
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-rbd}
Provides:	python-rbd = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-rbd < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-rbd
This package contains Python 3 libraries for interacting with Ceph RADOS
block device.

%package -n libcephfs2
Summary:	Ceph distributed file system client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Obsoletes:	libcephfs1 < %{_epoch_prefix}%{version}-%{release}
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-libcephfs
%endif
%description -n libcephfs2
Ceph is a distributed network file system designed to provide excellent
performance, reliability, and scalability. This is a shared library
allowing applications to access a Ceph distributed file system via a
POSIX-like interface.

%package -n libcephfs-devel
Summary:	Ceph distributed file system headers
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librados-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-devel < %{_epoch_prefix}%{version}-%{release}
Provides:	libcephfs2-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	libcephfs2-devel < %{_epoch_prefix}%{version}-%{release}
%description -n libcephfs-devel
This package contains libraries and headers needed to develop programs
that use Ceph distributed file system.

%package -n python%{python3_pkgversion}-cephfs
Summary:	Python 3 libraries for Ceph distributed file system
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-ceph-argparse = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-cephfs}
Provides:	python-cephfs = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-cephfs < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-cephfs
This package contains Python 3 libraries for interacting with Ceph distributed
file system.

%package -n python%{python3_pkgversion}-ceph-argparse
Summary:	Python 3 utility libraries for Ceph CLI
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
%{?python_provide:%python_provide python%{python3_pkgversion}-ceph-argparse}
%description -n python%{python3_pkgversion}-ceph-argparse
This package contains types and routines for Python 3 used by the Ceph CLI as
well as the RESTful interface. These have to do with querying the daemons for
command-description information, validating user command input against those
descriptions, and submitting the command to the appropriate daemon.

%package -n python%{python3_pkgversion}-ceph-common
Summary:	Python 3 utility libraries for Ceph
%if 0%{?fedora} || 0%{?rhel} >= 8
Requires:       python%{python3_pkgversion}-pyyaml
%endif
%if 0%{?suse_version}
Requires:       python%{python3_pkgversion}-PyYAML
%endif
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
%{?python_provide:%python_provide python%{python3_pkgversion}-ceph-common}
%description -n python%{python3_pkgversion}-ceph-common
This package contains data structures, classes and functions used by Ceph.
It also contains utilities used for the cephadm orchestrator.

%if 0%{with cephfs_shell}
%package -n cephfs-shell
Summary:    Interactive shell for Ceph file system
Requires:   python%{python3_pkgversion}-cmd2
Requires:   python%{python3_pkgversion}-colorama
Requires:   python%{python3_pkgversion}-cephfs
%description -n cephfs-shell
This package contains an interactive tool that allows accessing a Ceph
file system without mounting it  by providing a nice pseudo-shell which
works like an FTP client.
%endif

%if 0%{with ceph_test_package}
%package -n ceph-test
Summary:	Ceph benchmarks and test tools
%if 0%{?suse_version}
Group:		System/Benchmark
%endif
Requires:	ceph-common = %{_epoch_prefix}%{version}-%{release}
Requires:	xmlstarlet
Requires:	jq
Requires:	socat
%description -n ceph-test
This package contains Ceph benchmarks and test tools.
%endif

%if 0%{with cephfs_java}

%package -n libcephfs_jni1
Summary:	Java Native Interface library for CephFS Java bindings
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	java
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
%description -n libcephfs_jni1
This package contains the Java Native Interface library for CephFS Java
bindings.

%package -n libcephfs_jni-devel
Summary:	Development files for CephFS Java Native Interface library
%if 0%{?suse_version}
Group:		Development/Libraries/Java
%endif
Requires:	java
Requires:	libcephfs_jni1 = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-devel < %{_epoch_prefix}%{version}-%{release}
Provides:	libcephfs_jni1-devel = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	libcephfs_jni1-devel < %{_epoch_prefix}%{version}-%{release}
%description -n libcephfs_jni-devel
This package contains the development files for CephFS Java Native Interface
library.

%package -n cephfs-java
Summary:	Java libraries for the Ceph File System
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	java
Requires:	libcephfs_jni1 = %{_epoch_prefix}%{version}-%{release}
Requires:       junit
BuildRequires:  junit
%description -n cephfs-java
This package contains the Java libraries for the Ceph File System.

%endif

%package -n rados-objclass-devel
Summary:        RADOS object class development kit
%if 0%{?suse_version}
Group:		Development/Libraries/C and C++
%endif
Requires:       libradospp-devel = %{_epoch_prefix}%{version}-%{release}
%description -n rados-objclass-devel
This package contains libraries and headers needed to develop RADOS object
class plugins.

%if 0%{with selinux}

%package selinux
Summary:	SELinux support for Ceph MON, OSD and MDS
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires:	policycoreutils, libselinux-utils
Requires(post):	ceph-base = %{_epoch_prefix}%{version}-%{release}
Requires(post): selinux-policy-base >= %{_selinux_policy_version}, policycoreutils, gawk
Requires(postun): policycoreutils
%description selinux
This package contains SELinux support for Ceph MON, OSD and MDS. The package
also performs file-system relabelling which can take a long time on heavily
populated file-systems.

%endif

%package grafana-dashboards
Summary:	The set of Grafana dashboards for monitoring purposes
BuildArch:	noarch
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
%description grafana-dashboards
This package provides a set of Grafana dashboards for monitoring of
Ceph clusters. The dashboards require a Prometheus server setup
collecting data from Ceph Manager "prometheus" module and Prometheus
project "node_exporter" module. The dashboards are designed to be
integrated with the Ceph Manager Dashboard web UI.

%package prometheus-alerts
Summary:        Prometheus alerts for a Ceph deployment
BuildArch:      noarch
Group:          System/Monitoring
%description prometheus-alerts
This package provides Ceph default alerts for Prometheus.

#################################################################################
# common
#################################################################################
%prep
%autosetup -p1 -n ceph-17.2.2

%build
# Disable lto on systems that do not support symver attribute
# See https://gcc.gnu.org/bugzilla/show_bug.cgi?id=48200 for details
%if ( 0%{?rhel} && 0%{?rhel} < 9 ) || ( 0%{?suse_version} && 0%{?suse_version} <= 1500 )
%define _lto_cflags %{nil}
%endif

%if 0%{with seastar} && 0%{?rhel}
. /opt/rh/gcc-toolset-9/enable
%endif

%if 0%{with cephfs_java}
# Find jni.h
for i in /usr/{lib64,lib}/jvm/java/include{,/linux}; do
    [ -d $i ] && java_inc="$java_inc -I$i"
done
%endif

%if 0%{?suse_version}
%limit_build -m 3000
%endif

export CPPFLAGS="$java_inc"
export CFLAGS="$RPM_OPT_FLAGS"
export CXXFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"

%if 0%{with seastar}
# seastar uses longjmp() to implement coroutine. and this annoys longjmp_chk()
export CXXFLAGS=$(echo $RPM_OPT_FLAGS | sed -e 's/-Wp,-D_FORTIFY_SOURCE=2//g')
# remove from CFLAGS too because it causes the arrow submodule to fail with:
#   warning _FORTIFY_SOURCE requires compiling with optimization (-O)
export CFLAGS=$(echo $RPM_OPT_FLAGS | sed -e 's/-Wp,-D_FORTIFY_SOURCE=2//g')
%endif

env | sort

%{?!_vpath_builddir:%global _vpath_builddir %{_target_platform}}

# TODO: drop this step once we can use `cmake -B`
mkdir -p %{_vpath_builddir}
pushd %{_vpath_builddir}
cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR:PATH=%{_libdir} \
    -DCMAKE_INSTALL_LIBEXECDIR:PATH=%{_libexecdir} \
    -DCMAKE_INSTALL_LOCALSTATEDIR:PATH=%{_localstatedir} \
    -DCMAKE_INSTALL_SYSCONFDIR:PATH=%{_sysconfdir} \
    -DCMAKE_INSTALL_MANDIR:PATH=%{_mandir} \
    -DCMAKE_INSTALL_DOCDIR:PATH=%{_docdir}/ceph \
    -DCMAKE_INSTALL_INCLUDEDIR:PATH=%{_includedir} \
    -DSYSTEMD_SYSTEM_UNIT_DIR:PATH=%{_unitdir} \
    -DWITH_MANPAGE:BOOL=ON \
    -DWITH_PYTHON3:STRING=%{python3_version} \
    -DWITH_MGR_DASHBOARD_FRONTEND:BOOL=OFF \
%if 0%{without ceph_test_package}
    -DWITH_TESTS:BOOL=OFF \
%endif
%if 0%{with cephfs_java}
    -DWITH_CEPHFS_JAVA:BOOL=ON \
%endif
%if 0%{with selinux}
    -DWITH_SELINUX:BOOL=ON \
%endif
%if %{with lttng}
    -DWITH_LTTNG:BOOL=ON \
    -DWITH_BABELTRACE:BOOL=ON \
%else
    -DWITH_LTTNG:BOOL=OFF \
    -DWITH_BABELTRACE:BOOL=OFF \
%endif
    $CEPH_EXTRA_CMAKE_ARGS \
%if 0%{with ocf}
    -DWITH_OCF:BOOL=ON \
%endif
%if 0%{with cephfs_shell}
    -DWITH_CEPHFS_SHELL:BOOL=ON \
%endif
%if 0%{with libradosstriper}
    -DWITH_LIBRADOSSTRIPER:BOOL=ON \
%else
    -DWITH_LIBRADOSSTRIPER:BOOL=OFF \
%endif
%if 0%{with amqp_endpoint}
    -DWITH_RADOSGW_AMQP_ENDPOINT:BOOL=ON \
%else
    -DWITH_RADOSGW_AMQP_ENDPOINT:BOOL=OFF \
%endif
%if 0%{with kafka_endpoint}
    -DWITH_RADOSGW_KAFKA_ENDPOINT:BOOL=ON \
%else
    -DWITH_RADOSGW_KAFKA_ENDPOINT:BOOL=OFF \
%endif
%if 0%{without lua_packages}
    -DWITH_RADOSGW_LUA_PACKAGES:BOOL=OFF \
%endif
%if 0%{with zbd}
    -DWITH_ZBD:BOOL=ON \
%endif
%if 0%{with cmake_verbose_logging}
    -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON \
%endif
%if 0%{with rbd_rwl_cache}
    -DWITH_RBD_RWL:BOOL=ON \
%endif
%if 0%{with rbd_ssd_cache}
    -DWITH_RBD_SSD_CACHE:BOOL=ON \
%endif
%if 0%{with system_pmdk}
    -DWITH_SYSTEM_PMDK:BOOL=ON \
%endif
%if 0%{with jaeger}
    -DWITH_JAEGER:BOOL=ON \
%endif
%if 0%{?suse_version}
    -DBOOST_J:STRING=%{jobs} \
%else
    -DBOOST_J:STRING=%{_smp_build_ncpus} \
%endif
%if 0%{?rhel}
    -DWITH_FMT_HEADER_ONLY:BOOL=ON \
%endif
%if 0%{with system_arrow}
    -DWITH_SYSTEM_ARROW:BOOL=ON \
%endif
%if 0%{with system_utf8proc}
    -DWITH_SYSTEM_UTF8PROC:BOOL=ON \
%endif
    -DWITH_GRAFANA:BOOL=ON

%if %{with cmake_verbose_logging}
cat ./CMakeFiles/CMakeOutput.log
cat ./CMakeFiles/CMakeError.log
%endif

%if 0%{?suse_version}
make %{_smp_mflags}
%else
%make_build
%endif

popd

%if 0%{with make_check}
%check
# run in-tree unittests
pushd %{_vpath_builddir}
ctest %{_smp_mflags}
popd
%endif


%install
pushd %{_vpath_builddir}
%make_install
# we have dropped sysvinit bits
rm -f %{buildroot}/%{_sysconfdir}/init.d/ceph
popd

%if 0%{with seastar}
# package crimson-osd with the name of ceph-osd
install -m 0755 %{buildroot}%{_bindir}/crimson-osd %{buildroot}%{_bindir}/ceph-osd
%endif

install -m 0644 -D src/etc-rbdmap %{buildroot}%{_sysconfdir}/ceph/rbdmap
%if 0%{?fedora} || 0%{?rhel}
install -m 0644 -D etc/sysconfig/ceph %{buildroot}%{_sysconfdir}/sysconfig/ceph
%endif
%if 0%{?suse_version}
install -m 0644 -D etc/sysconfig/ceph %{buildroot}%{_fillupdir}/sysconfig.%{name}
%endif
install -m 0644 -D systemd/ceph.tmpfiles.d %{buildroot}%{_tmpfilesdir}/ceph-common.conf
install -m 0644 -D systemd/50-ceph.preset %{buildroot}%{_presetdir}/50-ceph.preset
mkdir -p %{buildroot}%{_sbindir}
install -m 0644 -D src/logrotate.conf %{buildroot}%{_sysconfdir}/logrotate.d/ceph
chmod 0644 %{buildroot}%{_docdir}/ceph/sample.ceph.conf
install -m 0644 -D COPYING %{buildroot}%{_docdir}/ceph/COPYING
install -m 0644 -D etc/sysctl/90-ceph-osd.conf %{buildroot}%{_sysctldir}/90-ceph-osd.conf
install -m 0755 -D src/tools/rbd_nbd/rbd-nbd_quiesce %{buildroot}%{_libexecdir}/rbd-nbd/rbd-nbd_quiesce

install -m 0755 src/cephadm/cephadm %{buildroot}%{_sbindir}/cephadm
mkdir -p %{buildroot}%{_sharedstatedir}/cephadm
chmod 0700 %{buildroot}%{_sharedstatedir}/cephadm
mkdir -p %{buildroot}%{_sharedstatedir}/cephadm/.ssh
chmod 0700 %{buildroot}%{_sharedstatedir}/cephadm/.ssh
touch %{buildroot}%{_sharedstatedir}/cephadm/.ssh/authorized_keys
chmod 0600 %{buildroot}%{_sharedstatedir}/cephadm/.ssh/authorized_keys

# firewall templates and /sbin/mount.ceph symlink
%if 0%{?suse_version} && !0%{?usrmerged}
mkdir -p %{buildroot}/sbin
ln -sf %{_sbindir}/mount.ceph %{buildroot}/sbin/mount.ceph
%endif

# udev rules
install -m 0644 -D udev/50-rbd.rules %{buildroot}%{_udevrulesdir}/50-rbd.rules

# sudoers.d
install -m 0440 -D sudoers.d/ceph-smartctl %{buildroot}%{_sysconfdir}/sudoers.d/ceph-smartctl

%if 0%{?rhel} >= 8
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" %{buildroot}%{_bindir}/*
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" %{buildroot}%{_sbindir}/*
%endif

#set up placeholder directories
mkdir -p %{buildroot}%{_sysconfdir}/ceph
mkdir -p %{buildroot}%{_localstatedir}/run/ceph
mkdir -p %{buildroot}%{_localstatedir}/log/ceph
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/tmp
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/mon
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/osd
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/mds
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/mgr
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/crash
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/crash/posted
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/radosgw
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-osd
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-mds
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-rgw
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-mgr
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-rbd
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-rbd-mirror

# prometheus alerts
install -m 644 -D monitoring/ceph-mixin/prometheus_alerts.yml %{buildroot}/etc/prometheus/ceph/ceph_default_alerts.yml

%if 0%{?suse_version}
# create __pycache__ directories and their contents
%py3_compile %{buildroot}%{python3_sitelib}
# hardlink duplicate files under /usr to save space
%fdupes %{buildroot}%{_prefix}
%endif

%if 0%{?rhel} == 8
%py_byte_compile %{__python3} %{buildroot}%{python3_sitelib}
%endif

%clean
rm -rf %{buildroot}
# built binaries are no longer necessary at this point,
# but are consuming ~17GB of disk in the build environment
rm -rf %{_vpath_builddir}

#################################################################################
# files and systemd scriptlets
#################################################################################
%files

%files base
%{_bindir}/ceph-crash
%{_bindir}/crushtool
%{_bindir}/monmaptool
%{_bindir}/osdmaptool
%{_bindir}/ceph-kvstore-tool
%{_bindir}/ceph-run
%{_presetdir}/50-ceph.preset
%{_sbindir}/ceph-create-keys
%dir %{_libexecdir}/ceph
%{_libexecdir}/ceph/ceph_common.sh
%dir %{_libdir}/rados-classes
%{_libdir}/rados-classes/*
%dir %{_libdir}/ceph
%dir %{_libdir}/ceph/erasure-code
%{_libdir}/ceph/erasure-code/libec_*.so*
%dir %{_libdir}/ceph/compressor
%{_libdir}/ceph/compressor/libceph_*.so*
%{_unitdir}/ceph-crash.service
%dir %{_libdir}/ceph/crypto
%{_libdir}/ceph/crypto/libceph_*.so*
%if %{with lttng}
%{_libdir}/libos_tp.so*
%{_libdir}/libosd_tp.so*
%endif
%config(noreplace) %{_sysconfdir}/logrotate.d/ceph
%if 0%{?fedora} || 0%{?rhel}
%config(noreplace) %{_sysconfdir}/sysconfig/ceph
%endif
%if 0%{?suse_version}
%{_fillupdir}/sysconfig.*
%endif
%{_unitdir}/ceph.target
%{_mandir}/man8/ceph-create-keys.8*
%{_mandir}/man8/ceph-run.8*
%{_mandir}/man8/crushtool.8*
%{_mandir}/man8/osdmaptool.8*
%{_mandir}/man8/monmaptool.8*
%{_mandir}/man8/ceph-kvstore-tool.8*
#set up placeholder directories
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/crash
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/crash/posted
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/tmp
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-osd
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-mds
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rgw
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-mgr
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rbd
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rbd-mirror
%{_sysconfdir}/sudoers.d/ceph-smartctl

%post base
/sbin/ldconfig
%if 0%{?suse_version}
%fillup_only
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl preset ceph.target ceph-crash.service >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph.target ceph-crash.service
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph.target ceph-crash.service >/dev/null 2>&1 || :
fi

%preun base
%if 0%{?suse_version}
%service_del_preun ceph.target ceph-crash.service
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph.target ceph-crash.service
%endif

%postun base
/sbin/ldconfig
%systemd_postun ceph.target

%pre -n cephadm
getent group cephadm >/dev/null || groupadd -r cephadm
getent passwd cephadm >/dev/null || useradd -r -g cephadm -s /bin/bash -c "cephadm user for mgr/cephadm" -d %{_sharedstatedir}/cephadm cephadm
exit 0

%if ! 0%{?suse_version}
%postun -n cephadm
userdel -r cephadm || true
exit 0
%endif

%files -n cephadm
%{_sbindir}/cephadm
%{_mandir}/man8/cephadm.8*
%attr(0700,cephadm,cephadm) %dir %{_sharedstatedir}/cephadm
%attr(0700,cephadm,cephadm) %dir %{_sharedstatedir}/cephadm/.ssh
%config(noreplace) %attr(0600,cephadm,cephadm) %{_sharedstatedir}/cephadm/.ssh/authorized_keys

%files common
%dir %{_docdir}/ceph
%doc %{_docdir}/ceph/sample.ceph.conf
%license %{_docdir}/ceph/COPYING
%{_bindir}/ceph
%{_bindir}/ceph-authtool
%{_bindir}/ceph-conf
%{_bindir}/ceph-dencoder
%{_bindir}/ceph-rbdnamer
%{_bindir}/ceph-syn
%{_bindir}/cephfs-data-scan
%{_bindir}/cephfs-journal-tool
%{_bindir}/cephfs-table-tool
%{_bindir}/crushdiff
%{_bindir}/rados
%{_bindir}/radosgw-admin
%{_bindir}/rbd
%{_bindir}/rbd-replay
%{_bindir}/rbd-replay-many
%{_bindir}/rbdmap
%{_sbindir}/mount.ceph
%if 0%{?suse_version} && !0%{?usrmerged}
/sbin/mount.ceph
%endif
%if %{with lttng}
%{_bindir}/rbd-replay-prep
%endif
%{_bindir}/ceph-post-file
%dir %{_libdir}/ceph/denc
%{_libdir}/ceph/denc/denc-mod-*.so
%{_tmpfilesdir}/ceph-common.conf
%{_mandir}/man8/ceph-authtool.8*
%{_mandir}/man8/ceph-conf.8*
%{_mandir}/man8/ceph-dencoder.8*
%{_mandir}/man8/ceph-diff-sorted.8*
%{_mandir}/man8/ceph-rbdnamer.8*
%{_mandir}/man8/ceph-syn.8*
%{_mandir}/man8/ceph-post-file.8*
%{_mandir}/man8/ceph.8*
%{_mandir}/man8/crushdiff.8*
%{_mandir}/man8/mount.ceph.8*
%{_mandir}/man8/rados.8*
%{_mandir}/man8/radosgw-admin.8*
%{_mandir}/man8/rbd.8*
%{_mandir}/man8/rbdmap.8*
%{_mandir}/man8/rbd-replay.8*
%{_mandir}/man8/rbd-replay-many.8*
%{_mandir}/man8/rbd-replay-prep.8*
%{_mandir}/man8/rgw-orphan-list.8*
%dir %{_datadir}/ceph/
%{_datadir}/ceph/known_hosts_drop.ceph.com
%{_datadir}/ceph/id_rsa_drop.ceph.com
%{_datadir}/ceph/id_rsa_drop.ceph.com.pub
%dir %{_sysconfdir}/ceph/
%config %{_sysconfdir}/bash_completion.d/ceph
%config %{_sysconfdir}/bash_completion.d/rados
%config %{_sysconfdir}/bash_completion.d/rbd
%config %{_sysconfdir}/bash_completion.d/radosgw-admin
%config(noreplace) %{_sysconfdir}/ceph/rbdmap
%{_unitdir}/rbdmap.service
%dir %{_udevrulesdir}
%{_udevrulesdir}/50-rbd.rules
%attr(3770,ceph,ceph) %dir %{_localstatedir}/log/ceph/
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/

%pre common
CEPH_GROUP_ID=167
CEPH_USER_ID=167
%if 0%{?rhel} || 0%{?fedora}
/usr/sbin/groupadd ceph -g $CEPH_GROUP_ID -o -r 2>/dev/null || :
/usr/sbin/useradd ceph -u $CEPH_USER_ID -o -r -g ceph -s /sbin/nologin -c "Ceph daemons" -d %{_localstatedir}/lib/ceph 2>/dev/null || :
%endif
%if 0%{?suse_version}
if ! getent group ceph >/dev/null ; then
    CEPH_GROUP_ID_OPTION=""
    getent group $CEPH_GROUP_ID >/dev/null || CEPH_GROUP_ID_OPTION="-g $CEPH_GROUP_ID"
    groupadd ceph $CEPH_GROUP_ID_OPTION -r 2>/dev/null || :
fi
if ! getent passwd ceph >/dev/null ; then
    CEPH_USER_ID_OPTION=""
    getent passwd $CEPH_USER_ID >/dev/null || CEPH_USER_ID_OPTION="-u $CEPH_USER_ID"
    useradd ceph $CEPH_USER_ID_OPTION -r -g ceph -s /sbin/nologin 2>/dev/null || :
fi
usermod -c "Ceph storage service" \
        -d %{_localstatedir}/lib/ceph \
        -g ceph \
        -s /sbin/nologin \
        ceph
%endif
exit 0

%post common
%tmpfiles_create %{_tmpfilesdir}/ceph-common.conf

%postun common
# Package removal cleanup
if [ "$1" -eq "0" ] ; then
    rm -rf %{_localstatedir}/log/ceph
    rm -rf %{_sysconfdir}/ceph
fi

%files mds
%{_bindir}/ceph-mds
%{_mandir}/man8/ceph-mds.8*
%{_unitdir}/ceph-mds@.service
%{_unitdir}/ceph-mds.target
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/mds

%post mds
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-mds@\*.service ceph-mds.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-mds@\*.service ceph-mds.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-mds.target >/dev/null 2>&1 || :
fi

%preun mds
%if 0%{?suse_version}
%service_del_preun ceph-mds@\*.service ceph-mds.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-mds@\*.service ceph-mds.target
%endif

%postun mds
%systemd_postun ceph-mds@\*.service ceph-mds.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-mds@\*.service > /dev/null 2>&1 || :
  fi
fi

%files mgr
%{_bindir}/ceph-mgr
%dir %{_datadir}/ceph/mgr
%{_datadir}/ceph/mgr/mgr_module.*
%{_datadir}/ceph/mgr/mgr_util.*
%{_datadir}/ceph/mgr/object_format.*
%{_unitdir}/ceph-mgr@.service
%{_unitdir}/ceph-mgr.target
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/mgr

%post mgr
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-mgr@\*.service ceph-mgr.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-mgr@\*.service ceph-mgr.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-mgr.target >/dev/null 2>&1 || :
fi

%preun mgr
%if 0%{?suse_version}
%service_del_preun ceph-mgr@\*.service ceph-mgr.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-mgr@\*.service ceph-mgr.target
%endif

%postun mgr
%systemd_postun ceph-mgr@\*.service ceph-mgr.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-mgr@\*.service > /dev/null 2>&1 || :
  fi
fi

%files mgr-dashboard
%{_datadir}/ceph/mgr/dashboard

%post mgr-dashboard
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%postun mgr-dashboard
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%files mgr-diskprediction-local
%{_datadir}/ceph/mgr/diskprediction_local

%post mgr-diskprediction-local
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%postun mgr-diskprediction-local
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%files mgr-modules-core
%dir %{_datadir}/ceph/mgr
%{_datadir}/ceph/mgr/alerts
%{_datadir}/ceph/mgr/balancer
%{_datadir}/ceph/mgr/crash
%{_datadir}/ceph/mgr/devicehealth
%{_datadir}/ceph/mgr/influx
%{_datadir}/ceph/mgr/insights
%{_datadir}/ceph/mgr/iostat
%{_datadir}/ceph/mgr/localpool
%{_datadir}/ceph/mgr/mds_autoscaler
%{_datadir}/ceph/mgr/mirroring
%{_datadir}/ceph/mgr/nfs
%{_datadir}/ceph/mgr/orchestrator
%{_datadir}/ceph/mgr/osd_perf_query
%{_datadir}/ceph/mgr/osd_support
%{_datadir}/ceph/mgr/pg_autoscaler
%{_datadir}/ceph/mgr/progress
%{_datadir}/ceph/mgr/prometheus
%{_datadir}/ceph/mgr/rbd_support
%{_datadir}/ceph/mgr/restful
%{_datadir}/ceph/mgr/selftest
%{_datadir}/ceph/mgr/snap_schedule
%{_datadir}/ceph/mgr/stats
%{_datadir}/ceph/mgr/status
%{_datadir}/ceph/mgr/telegraf
%{_datadir}/ceph/mgr/telemetry
%{_datadir}/ceph/mgr/test_orchestrator
%{_datadir}/ceph/mgr/volumes
%{_datadir}/ceph/mgr/zabbix

%files mgr-rook
%{_datadir}/ceph/mgr/rook

%post mgr-rook
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%postun mgr-rook
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%files mgr-k8sevents
%{_datadir}/ceph/mgr/k8sevents

%post mgr-k8sevents
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%postun mgr-k8sevents
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%files mgr-cephadm
%{_datadir}/ceph/mgr/cephadm

%post mgr-cephadm
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%postun mgr-cephadm
if [ $1 -eq 1 ] ; then
    /usr/bin/systemctl try-restart ceph-mgr.target >/dev/null 2>&1 || :
fi

%files mon
%{_bindir}/ceph-mon
%{_bindir}/ceph-monstore-tool
%{_mandir}/man8/ceph-mon.8*
%{_unitdir}/ceph-mon@.service
%{_unitdir}/ceph-mon.target
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/mon

%post mon
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-mon@\*.service ceph-mon.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-mon@\*.service ceph-mon.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-mon.target >/dev/null 2>&1 || :
fi

%preun mon
%if 0%{?suse_version}
%service_del_preun ceph-mon@\*.service ceph-mon.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-mon@\*.service ceph-mon.target
%endif

%postun mon
%systemd_postun ceph-mon@\*.service ceph-mon.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-mon@\*.service > /dev/null 2>&1 || :
  fi
fi

%files fuse
%{_bindir}/ceph-fuse
%{_mandir}/man8/ceph-fuse.8*
%{_sbindir}/mount.fuse.ceph
%{_mandir}/man8/mount.fuse.ceph.8*
%{_unitdir}/ceph-fuse@.service
%{_unitdir}/ceph-fuse.target

%files -n cephfs-mirror
%{_bindir}/cephfs-mirror
%{_mandir}/man8/cephfs-mirror.8*
%{_unitdir}/cephfs-mirror@.service
%{_unitdir}/cephfs-mirror.target

%post -n cephfs-mirror
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset cephfs-mirror@\*.service cephfs-mirror.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post cephfs-mirror@\*.service cephfs-mirror.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start cephfs-mirror.target >/dev/null 2>&1 || :
fi

%preun -n cephfs-mirror
%if 0%{?suse_version}
%service_del_preun cephfs-mirror@\*.service cephfs-mirror.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun cephfs-mirror@\*.service cephfs-mirror.target
%endif

%postun -n cephfs-mirror
%systemd_postun cephfs-mirror@\*.service cephfs-mirror.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart cephfs-mirror@\*.service > /dev/null 2>&1 || :
  fi
fi

%files -n rbd-fuse
%{_bindir}/rbd-fuse
%{_mandir}/man8/rbd-fuse.8*

%files -n rbd-mirror
%{_bindir}/rbd-mirror
%{_mandir}/man8/rbd-mirror.8*
%{_unitdir}/ceph-rbd-mirror@.service
%{_unitdir}/ceph-rbd-mirror.target

%post -n rbd-mirror
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-rbd-mirror@\*.service ceph-rbd-mirror.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-rbd-mirror@\*.service ceph-rbd-mirror.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-rbd-mirror.target >/dev/null 2>&1 || :
fi

%preun -n rbd-mirror
%if 0%{?suse_version}
%service_del_preun ceph-rbd-mirror@\*.service ceph-rbd-mirror.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-rbd-mirror@\*.service ceph-rbd-mirror.target
%endif

%postun -n rbd-mirror
%systemd_postun ceph-rbd-mirror@\*.service ceph-rbd-mirror.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-rbd-mirror@\*.service > /dev/null 2>&1 || :
  fi
fi

%files immutable-object-cache
%{_bindir}/ceph-immutable-object-cache
%{_mandir}/man8/ceph-immutable-object-cache.8*
%{_unitdir}/ceph-immutable-object-cache@.service
%{_unitdir}/ceph-immutable-object-cache.target

%post immutable-object-cache
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-immutable-object-cache@\*.service ceph-immutable-object-cache.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-immutable-object-cache@\*.service ceph-immutable-object-cache.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-immutable-object-cache.target >/dev/null 2>&1 || :
fi

%preun immutable-object-cache
%if 0%{?suse_version}
%service_del_preun ceph-immutable-object-cache@\*.service ceph-immutable-object-cache.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-immutable-object-cache@\*.service ceph-immutable-object-cache.target
%endif

%postun immutable-object-cache
%systemd_postun ceph-immutable-object-cache@\*.service ceph-immutable-object-cache.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-immutable-object-cache@\*.service > /dev/null 2>&1 || :
  fi
fi

%files -n rbd-nbd
%{_bindir}/rbd-nbd
%{_mandir}/man8/rbd-nbd.8*
%dir %{_libexecdir}/rbd-nbd
%{_libexecdir}/rbd-nbd/rbd-nbd_quiesce

%files radosgw
%{_bindir}/ceph-diff-sorted
%{_bindir}/radosgw
%{_bindir}/radosgw-token
%{_bindir}/radosgw-es
%{_bindir}/radosgw-object-expirer
%{_bindir}/rgw-gap-list
%{_bindir}/rgw-gap-list-comparator
%{_bindir}/rgw-orphan-list
%{_libdir}/libradosgw.so*
%{_mandir}/man8/radosgw.8*
%dir %{_localstatedir}/lib/ceph/radosgw
%{_unitdir}/ceph-radosgw@.service
%{_unitdir}/ceph-radosgw.target

%post radosgw
/sbin/ldconfig
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-radosgw@\*.service ceph-radosgw.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-radosgw@\*.service ceph-radosgw.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-radosgw.target >/dev/null 2>&1 || :
fi

%preun radosgw
%if 0%{?suse_version}
%service_del_preun ceph-radosgw@\*.service ceph-radosgw.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-radosgw@\*.service ceph-radosgw.target
%endif

%postun radosgw
/sbin/ldconfig
%systemd_postun ceph-radosgw@\*.service ceph-radosgw.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-radosgw@\*.service > /dev/null 2>&1 || :
  fi
fi

%files osd
%{_bindir}/ceph-clsinfo
%{_bindir}/ceph-bluestore-tool
%{_bindir}/ceph-erasure-code-tool
%{_bindir}/ceph-objectstore-tool
%{_bindir}/ceph-osdomap-tool
%{_bindir}/ceph-osd
%{_libexecdir}/ceph/ceph-osd-prestart.sh
%{_mandir}/man8/ceph-clsinfo.8*
%{_mandir}/man8/ceph-osd.8*
%{_mandir}/man8/ceph-bluestore-tool.8*
%{_unitdir}/ceph-osd@.service
%{_unitdir}/ceph-osd.target
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/osd
%config(noreplace) %{_sysctldir}/90-ceph-osd.conf

%post osd
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-osd@\*.service ceph-osd.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-osd@\*.service ceph-osd.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-osd.target >/dev/null 2>&1 || :
fi
%if 0%{?sysctl_apply}
    %sysctl_apply 90-ceph-osd.conf
%else
    /usr/lib/systemd/systemd-sysctl %{_sysctldir}/90-ceph-osd.conf > /dev/null 2>&1 || :
%endif

%preun osd
%if 0%{?suse_version}
%service_del_preun ceph-osd@\*.service ceph-osd.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-osd@\*.service ceph-osd.target
%endif

%postun osd
%systemd_postun ceph-osd@\*.service ceph-volume@\*.service ceph-osd.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-osd@\*.service ceph-volume@\*.service > /dev/null 2>&1 || :
  fi
fi

%if 0%{with seastar}
%files crimson-osd
%{_bindir}/crimson-osd
%endif

%files volume
%{_sbindir}/ceph-volume
%{_sbindir}/ceph-volume-systemd
%dir %{python3_sitelib}/ceph_volume
%{python3_sitelib}/ceph_volume/*
%{python3_sitelib}/ceph_volume-*
%{_mandir}/man8/ceph-volume.8*
%{_mandir}/man8/ceph-volume-systemd.8*
%{_unitdir}/ceph-volume@.service

%post volume
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-volume@\*.service >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-volume@\*.service
%endif

%preun volume
%if 0%{?suse_version}
%service_del_preun ceph-volume@\*.service
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-volume@\*.service
%endif

%postun volume
%systemd_postun ceph-volume@\*.service
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-volume@\*.service > /dev/null 2>&1 || :
  fi
fi

%if %{with ocf}

%files resource-agents
%dir %{_prefix}/lib/ocf
%dir %{_prefix}/lib/ocf/resource.d
%dir %{_prefix}/lib/ocf/resource.d/ceph
%attr(0755,-,-) %{_prefix}/lib/ocf/resource.d/ceph/rbd

%endif

%files -n librados2
%{_libdir}/librados.so.*
%dir %{_libdir}/ceph
%{_libdir}/ceph/libceph-common.so.*
%if %{with lttng}
%{_libdir}/librados_tp.so.*
%endif
%dir %{_sysconfdir}/ceph

%post -n librados2 -p /sbin/ldconfig

%postun -n librados2 -p /sbin/ldconfig

%files -n librados-devel
%dir %{_includedir}/rados
%{_includedir}/rados/librados.h
%{_includedir}/rados/rados_types.h
%{_libdir}/librados.so
%if %{with lttng}
%{_libdir}/librados_tp.so
%endif
%{_bindir}/librados-config
%{_mandir}/man8/librados-config.8*

%files -n libradospp-devel
%dir %{_includedir}/rados
%{_includedir}/rados/buffer.h
%{_includedir}/rados/buffer_fwd.h
%{_includedir}/rados/crc32c.h
%{_includedir}/rados/inline_memory.h
%{_includedir}/rados/librados.hpp
%{_includedir}/rados/librados_fwd.hpp
%{_includedir}/rados/page.h
%{_includedir}/rados/rados_types.hpp

%files -n python%{python3_pkgversion}-rados
%{python3_sitearch}/rados.cpython*.so
%{python3_sitearch}/rados-*.egg-info

%files -n libcephsqlite
%{_libdir}/libcephsqlite.so

%post -n libcephsqlite -p /sbin/ldconfig

%postun -n libcephsqlite -p /sbin/ldconfig

%files -n libcephsqlite-devel
%{_includedir}/libcephsqlite.h

%if 0%{with libradosstriper}
%files -n libradosstriper1
%{_libdir}/libradosstriper.so.*

%post -n libradosstriper1 -p /sbin/ldconfig

%postun -n libradosstriper1 -p /sbin/ldconfig

%files -n libradosstriper-devel
%dir %{_includedir}/radosstriper
%{_includedir}/radosstriper/libradosstriper.h
%{_includedir}/radosstriper/libradosstriper.hpp
%{_libdir}/libradosstriper.so
%endif

%files -n librbd1
%{_libdir}/librbd.so.*
%if %{with lttng}
%{_libdir}/librbd_tp.so.*
%endif
%dir %{_libdir}/ceph/librbd
%{_libdir}/ceph/librbd/libceph_*.so*

%post -n librbd1 -p /sbin/ldconfig

%postun -n librbd1 -p /sbin/ldconfig

%files -n librbd-devel
%dir %{_includedir}/rbd
%{_includedir}/rbd/librbd.h
%{_includedir}/rbd/librbd.hpp
%{_includedir}/rbd/features.h
%{_libdir}/librbd.so
%if %{with lttng}
%{_libdir}/librbd_tp.so
%endif

%files -n librgw2
%{_libdir}/librgw.so.*
%if %{with lttng}
%{_libdir}/librgw_op_tp.so.*
%{_libdir}/librgw_rados_tp.so.*
%endif

%post -n librgw2 -p /sbin/ldconfig

%postun -n librgw2 -p /sbin/ldconfig

%files -n librgw-devel
%dir %{_includedir}/rados
%{_includedir}/rados/librgw.h
%{_includedir}/rados/rgw_file.h
%{_libdir}/librgw.so
%if %{with lttng}
%{_libdir}/librgw_op_tp.so
%{_libdir}/librgw_rados_tp.so
%endif

%files -n python%{python3_pkgversion}-rgw
%{python3_sitearch}/rgw.cpython*.so
%{python3_sitearch}/rgw-*.egg-info

%files -n python%{python3_pkgversion}-rbd
%{python3_sitearch}/rbd.cpython*.so
%{python3_sitearch}/rbd-*.egg-info

%files -n libcephfs2
%{_libdir}/libcephfs.so.*
%dir %{_sysconfdir}/ceph

%post -n libcephfs2 -p /sbin/ldconfig

%postun -n libcephfs2 -p /sbin/ldconfig

%files -n libcephfs-devel
%dir %{_includedir}/cephfs
%{_includedir}/cephfs/libcephfs.h
%{_includedir}/cephfs/ceph_ll_client.h
%dir %{_includedir}/cephfs/metrics
%{_includedir}/cephfs/metrics/Types.h
%{_libdir}/libcephfs.so

%files -n python%{python3_pkgversion}-cephfs
%{python3_sitearch}/cephfs.cpython*.so
%{python3_sitearch}/cephfs-*.egg-info

%files -n python%{python3_pkgversion}-ceph-argparse
%{python3_sitelib}/ceph_argparse.py
%{python3_sitelib}/__pycache__/ceph_argparse.cpython*.py*
%{python3_sitelib}/ceph_daemon.py
%{python3_sitelib}/__pycache__/ceph_daemon.cpython*.py*

%files -n python%{python3_pkgversion}-ceph-common
%{python3_sitelib}/ceph
%{python3_sitelib}/ceph-*.egg-info

%if 0%{with cephfs_shell}
%files -n cephfs-shell
%{python3_sitelib}/cephfs_shell-*.egg-info
%{_bindir}/cephfs-shell
%{_mandir}/man8/cephfs-shell.8*
%endif

%files -n cephfs-top
%{python3_sitelib}/cephfs_top-*.egg-info
%{_bindir}/cephfs-top
%{_mandir}/man8/cephfs-top.8*

%if 0%{with ceph_test_package}
%files -n ceph-test
%{_bindir}/ceph-client-debug
%{_bindir}/ceph_bench_log
%{_bindir}/ceph_multi_stress_watch
%{_bindir}/ceph_erasure_code_benchmark
%{_bindir}/ceph_omapbench
%{_bindir}/ceph_objectstore_bench
%{_bindir}/ceph_perf_objectstore
%{_bindir}/ceph_perf_local
%{_bindir}/ceph_perf_msgr_client
%{_bindir}/ceph_perf_msgr_server
%{_bindir}/ceph_psim
%{_bindir}/ceph_radosacl
%{_bindir}/ceph_rgw_jsonparser
%{_bindir}/ceph_rgw_multiparser
%{_bindir}/ceph_scratchtool
%{_bindir}/ceph_scratchtoolpp
%{_bindir}/ceph_test_*
%{_bindir}/ceph-coverage
%{_bindir}/ceph-debugpack
%{_bindir}/ceph-dedup-tool
%if 0%{with seastar}
%{_bindir}/crimson-store-nbd
%endif
%{_mandir}/man8/ceph-debugpack.8*
%dir %{_libdir}/ceph
%{_libdir}/ceph/ceph-monstore-update-crush.sh
%endif

%if 0%{with cephfs_java}
%files -n libcephfs_jni1
%{_libdir}/libcephfs_jni.so.*

%post -n libcephfs_jni1 -p /sbin/ldconfig

%postun -n libcephfs_jni1 -p /sbin/ldconfig

%files -n libcephfs_jni-devel
%{_libdir}/libcephfs_jni.so

%files -n cephfs-java
%{_javadir}/libcephfs.jar
%{_javadir}/libcephfs-test.jar
%endif

%files -n rados-objclass-devel
%dir %{_includedir}/rados
%{_includedir}/rados/objclass.h

%if 0%{with selinux}
%files selinux
%attr(0600,root,root) %{_datadir}/selinux/packages/ceph.pp
%{_datadir}/selinux/devel/include/contrib/ceph.if
%{_mandir}/man8/ceph_selinux.8*

%post selinux
# backup file_contexts before update
. /etc/selinux/config
FILE_CONTEXT=/etc/selinux/${SELINUXTYPE}/contexts/files/file_contexts
cp ${FILE_CONTEXT} ${FILE_CONTEXT}.pre

# Install the policy
/usr/sbin/semodule -i %{_datadir}/selinux/packages/ceph.pp

# Load the policy if SELinux is enabled
if ! /usr/sbin/selinuxenabled; then
    # Do not relabel if selinux is not enabled
    exit 0
fi

if diff ${FILE_CONTEXT} ${FILE_CONTEXT}.pre > /dev/null 2>&1; then
   # Do not relabel if file contexts did not change
   exit 0
fi

# Stop ceph.target while relabeling if CEPH_AUTO_RESTART_ON_UPGRADE=yes
SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
fi

# Check whether the daemons are running
/usr/bin/systemctl status ceph.target > /dev/null 2>&1
STATUS=$?

# Stop the daemons if they were running
if test $STATUS -eq 0; then
    if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
        /usr/bin/systemctl stop ceph.target > /dev/null 2>&1
    fi
fi

# Relabel the files fix for first package install
/usr/sbin/fixfiles -C ${FILE_CONTEXT}.pre restore 2> /dev/null

rm -f ${FILE_CONTEXT}.pre
# The fixfiles command won't fix label for /var/run/ceph
/usr/sbin/restorecon -R /var/run/ceph > /dev/null 2>&1

# Start the daemons iff they were running before
if test $STATUS -eq 0; then
    if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
        /usr/bin/systemctl start ceph.target > /dev/null 2>&1 || :
    fi
fi
exit 0

%postun selinux
if [ $1 -eq 0 ]; then
    # backup file_contexts before update
    . /etc/selinux/config
    FILE_CONTEXT=/etc/selinux/${SELINUXTYPE}/contexts/files/file_contexts
    cp ${FILE_CONTEXT} ${FILE_CONTEXT}.pre

    # Remove the module
    /usr/sbin/semodule -n -r ceph > /dev/null 2>&1

    # Reload the policy if SELinux is enabled
    if ! /usr/sbin/selinuxenabled ; then
        # Do not relabel if SELinux is not enabled
        exit 0
    fi

    # Stop ceph.target while relabeling if CEPH_AUTO_RESTART_ON_UPGRADE=yes
    SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
    if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
        source $SYSCONF_CEPH
    fi

    # Check whether the daemons are running
    /usr/bin/systemctl status ceph.target > /dev/null 2>&1
    STATUS=$?

    # Stop the daemons if they were running
    if test $STATUS -eq 0; then
        if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
            /usr/bin/systemctl stop ceph.target > /dev/null 2>&1
        fi
    fi

    /usr/sbin/fixfiles -C ${FILE_CONTEXT}.pre restore 2> /dev/null
    rm -f ${FILE_CONTEXT}.pre
    # The fixfiles command won't fix label for /var/run/ceph
    /usr/sbin/restorecon -R /var/run/ceph > /dev/null 2>&1

    # Start the daemons if they were running before
    if test $STATUS -eq 0; then
        if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
	    /usr/bin/systemctl start ceph.target > /dev/null 2>&1 || :
        fi
    fi
fi
exit 0
%endif

%files grafana-dashboards
%if 0%{?suse_version}
%attr(0755,root,root) %dir %{_sysconfdir}/grafana
%attr(0755,root,root) %dir %{_sysconfdir}/grafana/dashboards
%endif
%attr(0755,root,root) %dir %{_sysconfdir}/grafana/dashboards/ceph-dashboard
%config %{_sysconfdir}/grafana/dashboards/ceph-dashboard/*

%files prometheus-alerts
%if 0%{?suse_version}
%attr(0755,root,root) %dir %{_sysconfdir}/prometheus
%endif
%attr(0755,root,root) %dir %{_sysconfdir}/prometheus/ceph
%config %{_sysconfdir}/prometheus/ceph/ceph_default_alerts.yml

%changelog
