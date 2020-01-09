Name:               conman
Version:            0.2.7
Release:            12%{?dist}
Summary:            ConMan - The Console Manager

Group:              Applications/System
License:            GPLv2+
URL:                http://home.gna.org/conman/
Source0:            http://download.gna.org/%{name}/%{version}/%{name}-%{version}.tar.bz2
Source1:            %{name}.service
Source2:            %{name}.logrotate
Patch1:             conman-0.2.5-openfiles.patch
Patch2:             conman-0.2.5-strftime.patch
Patch3:             conman-0.2.7-num_threads.patch
BuildRoot:          %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires:           logrotate
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
BuildRequires:      tcp_wrappers
BuildRequires:      systemd-units
BuildRequires:      freeipmi-devel

%description
ConMan is a serial console management program designed to support a large
number of console devices and simultaneous users.  It currently supports
local serial devices and remote terminal servers (via the telnet protocol).
Its features include:

  - mapping symbolic names to console devices
  - logging all output from a console device to file
  - supporting monitor (R/O), interactive (R/W), and
    broadcast (W/O) modes of console access
  - allowing clients to join or steal console "write" privileges
  - executing Expect scripts across multiple consoles in parallel

%prep
%setup -q
%patch1 -b .openfiles -p1
%patch2 -b .strftime -p1
%patch3 -b .num_threads -p1

%build
# not really lib material, more like share
mv lib share
chmod -x share/examples/*.exp
%{__perl} -pi.orig -e 's|cd lib|cd share|g' \
    Makefile.in
%{__perl} -pi -e 's|lib\/|share\/|g' \
    Makefile.in share/examples/*.exp
# don't strip the bins on install, let find-debug.sh do it
%{__perl} -pi -e 's|-m 755 -s conman|-m 755 conman|g' \
    Makefile.in

%configure --with-tcp-wrappers
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
# put in our own initscript and logrotate
install -D -m 0644 %{SOURCE1} $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
rm -rf $RPM_BUILD_ROOT%{_sysconfdir}/init.d
install -m 0644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/%{name}
# make log directories
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/%{name}
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/%{name}.old
# examples don't belong in datadir...
rm -rf $RPM_BUILD_ROOT%{_datadir}/%{name}/examples
## these shouldn't be executable
#chmod -x $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}
# rhel7 uses systemd instead of sysV init, /etc/sysconfig/conman
# is not used. Remove it to reduce user's confusion:
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}
rmdir $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
# adjust perms on main config file
chmod 644 $RPM_BUILD_ROOT%{_sysconfdir}/%{name}.conf

%clean
rm -rf "$RPM_BUILD_ROOT"

%post
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable conman.service > /dev/null 2>&1 || :
    /bin/systemctl stop conman.service > /dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart conman.service >/dev/null 2>&1 || :
fi

%triggerun -- conman < 0.2.7-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply conman
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save conman >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del conman >/dev/null 2>&1 || :
/bin/systemctl try-restart conman.service >/dev/null 2>&1 || :

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING FAQ NEWS
%doc share/examples
%config(noreplace) %{_sysconfdir}/%{name}.conf
# rhel7 does not use this file:
#%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_unitdir}/%{name}.service
%{_localstatedir}/log/%{name}
%{_localstatedir}/log/%{name}.old
%{_bindir}/*
%{_sbindir}/*
%{_datadir}/%{name}
%{_mandir}/*/*

%changelog
* Fri Jul 17 2015 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-12
- Remove unused /etc/sysconfig/conman.
- Resolves: rhbz#1244219.

* Fri Jul 17 2015 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-11
- Ensure that num_threads <= IPMICONSOLE_THREAD_COUNT_MAX.
- Resolves: rhbz#1244189.

* Wed Jul  1 2015 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-10
- Enable IPMI feature.
- Resolves: rhbz#1084116.

* Wed Apr  8 2015 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-9
- Added commented-out "LimitNOFILE=" directive to conman.service.
- This is systemd-esque way to change process limits for serivces.
- Also and a comment when to use it.
- Resolves: rhbz#1035228.

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.2.7-8
- Mass rebuild 2014-01-24

* Tue Jan  7 2014 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-7
- Added "BuildRequires: systemd-units" to fix _unitdir expansion.
- Resolves: rhbz#1048854.

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.2.7-6
- Mass rebuild 2013-12-27

* Tue May  7 2013 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-5
- Again fixed "License:" in spec file (GPLv2+ -> GPLv3+).

* Tue May  7 2013 Denys Vlasenko <dvlasenk@redhat.com> - 0.2.7-4
- Forward-porting fixes from RHEL6.
- Enlarge buffer used for formatting date in a string format.
- Resolves: rhbz#891938.
- Allow configuration of the maximum number of open files.
- Resolves: rhbz#738967.

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 17 2012 Jon Ciesla <limburgher@gmail.com> - 0.2.7-1
- Migrate to systemd, BZ 771474.

* Sun Apr 15 2012 Steven M. Parrish <smparrish@gmail.com> - 0.2.7-0
- New upstream release

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jun 08 2009 Steven M. Parrish <tuxbrewr@fedoraproject.org> - 0.2.5-0
- New upstream release

* Mon Apr 20 2009 Steven M. Parrish <tuxbrewr@fedoraproject.org> - 0.2.4.1-1
- New upstream release

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Oct 06 2008 Jarod Wilson <jarod@redhat.com> 0.2.2-2
- The console option in conman.conf is case-insensitive, so relax
  defined consoles check in initscript (Mark McLoughlin, #465777)

* Mon Sep 08 2008 Steven M. Parrish <smparrish@shallowcreek.net> 0.2.2-1
- New upstream release

* Fri May 02 2008 Jarod Wilson <jwilson@redhat.com> 0.2.1-1
- New upstream release

* Wed Feb 13 2008 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-8
- Bump and rebuild for gcc 4.3

* Thu Apr 26 2007 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-7
- Update project urls
- Fix up initscript exit codes (#237936)

* Tue Sep 05 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-6
- Bump for new glibc

* Fri Jul 28 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-5
- Properly enable smp_mflags this time

* Fri Jul 28 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-4
- Add Reqs on chkconfig and service
- Turn on smp_mflags
- Initial build for RHEL5

* Wed Jul 05 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-3
- Add missing condrestart fuction to initscript

* Tue Jun 27 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-2
- Don't strip bins on make install, leave for find-debug.sh

* Tue Jun 27 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.2-1
- Update to 0.1.9.2

* Tue Jun 20 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.1-3
- Add Requires: logrotate
- Ugh, conmand exits cleanly if no CONSOLE(s) are defined in
  /etc/conman.conf, add check to initscript to report failure
  if none are defined

* Wed Jun 14 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.1-2
- Create log directories and install working logrotate config
- Use a much cleaner RH/FC-specific initscript

* Tue Jun 13 2006 Jarod Wilson <jwilson@redhat.com> 0.1.9.1-1
- Initial build for Fedora Extras
