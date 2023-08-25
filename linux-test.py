# Arch linux base install script
# Does not support partitioning yet

import subprocess, sys
from colorama import Fore

dev_mode = False

print('Starting Arch Linux base install script\n')

installation_options = {}
configure_boot_partition = False if not input('Do you want to configure boot partition? (N/y): ').lower() == 'y' else True

if (configure_boot_partition):
    installation_options['boot_partition'] = input('Enter what partition shall be used as boot partition: ')
else:
    installation_options['boot_partition'] = str()

installation_options['root_partition'] = input('Enter what partition shall be used as /root: ')
installation_options['swap_partition'] = input('Enter what partition shall be used as swap: ')
installation_options['hostname'] = input('Enter hostname (default "arch"): ') or 'arch'
installation_options['user_name'] = input('Enter username (default "simon"): ') or 'simon'
installation_options['password'] = input('Enter password (default "1234"): ') or '1234'
installation_options['keyboard_layout'] = 'sv-latin1'
installation_options['time_zone'] = '/usr/share/zoneinfo/Europe/Stockholm'

base_packages = (
    'base',
    'linux',
    'linux-firmware',
    'linux-headers',
    'nano',
    'vim'
    'networkmanager',
    'pipewire',
    'base-devel',
    'sudo',
    'openntpd'
)

if ((not installation_options['root_partition']) or (not installation_options['swap_partition'])):
    print(Fore.RED + 'No input was provided for root and (or) swap partition. Aborting.')
    sys.exit()

if ((not installation_options['boot_partition']) and (configure_boot_partition)):
    print(Fore.RED + 'No input was provided for boot partition. Aborting.')
    sys.exit()

print(Fore.YELLOW + 'Review installation options:' + Fore.WHITE)
for key, value in installation_options.items():
    print(f'{key}: {value}')

options_confirmed = input('Proceed with installation? (N/y)') or 'n'
if (options_confirmed.lower() != 'y'):
    print(Fore.RED + 'Installation options was not confirmed. Aborting.')
    sys.exit()

print(Fore.YELLOW + 'Review base packages:' + Fore.WHITE)
print('\n'.join(base_packages))

additional_packages = str()
proceed_with_extra_packages = input('Do you want to add additional packages? (N/y)') or 'n'
if (proceed_with_extra_packages.lower() == 'y'):
    additional_packages = input('Enter additional packages separated by SPACE: ')

all_packages = ' '.join(base_packages) if not additional_packages else ' '.join(base_packages) + ' ' + additional_packages
print(Fore.GREEN + 'Starting installation...' + Fore.WHITE)
print()
print('Format and mount root partition')
subprocess.Popen(f'mkfs.ext4 -F {installation_options["root_partition"]}', shell=True) if not dev_mode else print('Dev-mode: skipping format root partition')
subprocess.Popen(f'mount {installation_options["root_partition"]} /mnt', shell=True) if not dev_mode else print('Dev-mode: skipping mount root partition')
print(Fore.GREEN + 'OK' + Fore.WHITE)
print('Make swap on swap partition')
subprocess.Popen(f'mkswap {installation_options["swap_partition"]}', shell=True) if not dev_mode else print('Dev-mode: skipping mkswap')
print(Fore.GREEN + 'OK' + Fore.WHITE)
subprocess.Popen(f'swapon {installation_options["swap_partition"]}', shell=True) if not dev_mode else print('Dev-mode: skipping swapon')
print(Fore.GREEN + 'OK' + Fore.WHITE)

if (configure_boot_partition):
    print('Format boot partition')
    subprocess.Popen(f'mkfs.fat -F 32 {installation_options["boot_partition"]}', shell=True) if not dev_mode else print('Dev-mode: skipping format boot partition')
    subprocess.Popen(f'mkdir /mnt/boot', shell=True) if not dev_mode else print('Dev-mode: skipping create boot folder')
    subprocess.Popen(f'mount {installation_options["boot_partition"]} /mnt/boot', shell=True) if not dev_mode else print('Dev-mode: skipping mount boot partition')
    print(Fore.GREEN + 'OK' + Fore.WHITE)

print('Installing packages')
subprocess.Popen(f'pacstrap -K /mnt {all_packages}', shell=True) if not dev_mode else print('Dev-mode: skipping package installation')
print(Fore.GREEN + 'OK' + Fore.WHITE)
print('Make base configuration')
subprocess.Popen('genfstab -U /mnt >> /mnt/etc/fstab', shell=True) if not dev_mode else print('Dev-mode: skipping fstab config')
subprocess.Popen('arch-chroot /mnt', shell=True) if not dev_mode else print('Dev-mode: skipping enter arch-chroot')
subprocess.Popen(f'ln -sf {installation_options["time_zone"]} /etc/localtime', shell=True) if not dev_mode else print('Dev-mode: skipping time zone config')

if (not dev_mode):
    with open(r'/etc/locale.gen', 'r') as file:
        data = file.read()
        data = data.replace('#en_US.UTF8 UTF-8', 'en_US.UTF8 UTF-8')
        data = data.replace('#en_US ISO-8859-1', 'en_US ISO-8859-1')

    with open(r'/etc/locale.gen', 'w') as file:
        file.write(data)
    subprocess.Popen('locale-gen', shell=True)
    subprocess.Popen('echo "LANG=en_US.UTF-8" > /etc/locale.conf', shell=True)
    subprocess.Popen(f'echo "KEYMAP={installation_options["keyboard_layout"]}" > /etc/vconsole.conf', shell=True)
else:
    print('Dev-mode: skipping locale config')

subprocess.Popen(f'echo "{installation_options["hostname"]}" > /etc/hostname', shell=True) if not dev_mode else print('Dev-mode: skipping hostname config')
subprocess.Popen(f'echo "127.0.0.1\tlocalhost\n::1\t\t\tlocalhost\n127.0.0.1\t{installation_options["hostname"]}.localdomain\t{installation_options["hostname"]}" > /etc/hosts', shell=True) if not dev_mode else print('Dev-mode: skipping host file config')
print(Fore.GREEN + 'OK' + Fore.WHITE)

print('Enable services')
subprocess.Popen('systemctl enable NetworkManager', shell=True) if not dev_mode else print('Dev-mode: skipping enable NetworkManager')
subprocess.Popen('systemctl enable ntpd', shell=True) if not dev_mode else print('Dev-mode: skipping enable ntpd')
print(Fore.GREEN + 'OK' + Fore.WHITE)

print('Create user and add to sudoers')
if (not dev_mode):
    subprocess.Popen(f'useradd -m -G wheel -p "$(openssl passwd -1 {installation_options["password"]})" {installation_options["user_name"]}', shell=True)
    with open(r'/etc/sudoers', 'r') as file:
        data = file.read()
        data = data.replace('# %wheel ALL=(ALL:ALL) ALL', '%wheel ALL=(ALL:ALL) ALL')

    with open(r'/etc/sudoers', 'w') as file:
        file.write(data)
else:
    print('Dev-mode: skipping user config')
print(Fore.GREEN + 'OK' + Fore.WHITE)

if (configure_boot_partition):
    print('Configure systemd boot')
    subprocess.Popen('bootctl install', shell=True) if not dev_mode else print('Dev-mode: skipping systemd install')
    subprocess.Popen('echo "default\tarch.conf\ntimeout\t20\nconsole-mode\tmax\neditor\tno" > /boot/loader/loader.conf', shell=True) if not dev_mode else print('Dev-mode: skipping adding loader.conf')
    # find out partuuid
    subprocess.Popen('echo "title\tArch Linux\nlinux\t/vmlinuz-linux\ninitrd\t/initramfs-linux.img\noptions\troot=\"PARTUUID\" rw" > /boot/loader/entries/arch.conf', shell=True) if not dev_mode else print('Dev-mode: skipping adding arch.conf')
    print(Fore.GREEN + 'OK' + Fore.WHITE)

print('Exit arch-chroot')
subprocess.Popen('exit', shell=True) if not dev_mode else print('Dev-mode: skipping exit chroot')
print(Fore.GREEN + 'OK' + Fore.WHITE)
print(Fore.GREEN + '\nInstallation done, please reboot' + Fore.WHITE)