#!/bin/bash

# Variables
PART_BOOT='/dev/sda1'
PART_SWAP='/dev/sda2'
PART_ROOT='/dev/sda3'
HOSTNAME='archlinux'
USER_NAME='simon'
USER_PASSWORD='1234'
TIMEZONE='Europe/Stockholm'
TMP_ON_TMPFS='TRUE'
KEYMAP='sv-latin1'

# Choose your video driver
# For Intel
#VIDEO_DRIVER="i915"
# For nVidia
#VIDEO_DRIVER="nouveau"
# For ATI
#VIDEO_DRIVER="radeon"
# For generic stuff
VIDEO_DRIVER="vesa"

setup() {

    echo 'Formatting filesystems'
    format_filesystems

    echo 'Mounting filesystems'
    mount_filesystems

    echo 'Installing base system'
    install_base

    # echo 'Chrooting into installed system to continue setup...'
    # cp $0 /mnt/setup.sh
    # arch-chroot /mnt ./setup.sh chroot

    # if [ -f /mnt/setup.sh ]
    # then
    #     echo 'ERROR: Something failed inside the chroot, not unmounting filesystems so you can investigate.'
    #     echo 'Make sure you unmount everything before you try to run this script again.'
    # else
    #     echo 'Unmounting filesystems'
    #     unmount_filesystems
    #     echo 'Done! Reboot system.'
    # fi
    echo 'test done'
}

configure() {

    echo 'Installing additional packages'
    install_packages

    echo 'Clearing package tarballs'
    clean_packages

    echo 'Setting hostname'
    set_hostname "$HOSTNAME"

    echo 'Setting timezone'
    set_timezone "$TIMEZONE"

    echo 'Setting locale'
    set_locale

    echo 'Setting console keymap'
    set_keymap

    echo 'Setting hosts file'
    set_hosts "$HOSTNAME"

    echo 'Setting fstab'
    set_fstab

    echo 'Setting initial daemons'
    set_daemons

    echo 'Configuring sudo'
    set_sudoers

    if [ -z "$USER_PASSWORD" ]
    then
        echo "Enter the password for user $USER_NAME"
        stty -echo
        read USER_PASSWORD
        stty echo
    fi
    echo 'Creating initial user'
    create_user "$USER_NAME" "$USER_PASSWORD"
}

mount_filesystems() {

    mount /dev/$PART_ROOT /mnt
    mkdir /mnt/boot
    mount $PART_BOOT /mnt/boot
    swapon $PART_SWAP
}

install_base() {
    pacman -Sy
    pacstrap /mnt base base-devel linux linux-headers linux-firmware
}

unmount_filesystems() {
    umount /mnt/boot
    umount /mnt
}

install_packages() {
    local packages=''

    packages+= ' nano vim networkmanager pipewire sudo openntpd git'

    # # General utilities/libraries
    # packages+=' alsa-utils aspell-en chromium cpupower gvim mlocate net-tools ntp openssh p7zip pkgfile powertop python python2 rfkill rsync sudo unrar unzip wget zip systemd-sysvcompat zsh grml-zsh-config'

    # # Xserver
    # packages+=' xorg-apps xorg-server xorg-xinit xterm'


    if [ "$VIDEO_DRIVER" = "i915" ]
    then
        packages+=' xf86-video-intel libva-intel-driver'
    elif [ "$VIDEO_DRIVER" = "nouveau" ]
    then
        packages+=' xf86-video-nouveau'
    elif [ "$VIDEO_DRIVER" = "radeon" ]
    then
        packages+=' xf86-video-ati'
    elif [ "$VIDEO_DRIVER" = "vesa" ]
    then
        packages+=' xf86-video-vesa'
    fi

    pacman -Sy --noconfirm $packages
}

clean_packages() {
    yes | pacman -Scc
}

set_hostname() {
    local hostname="$1"; shift

    echo "$hostname" > /etc/hostname
}

set_timezone() {
    local timezone="$1"; shift

    ln -sT "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime
}

set_locale() {
    echo 'LANG="en_US.UTF-8"' >> /etc/locale.conf
    echo 'LC_COLLATE="C"' >> /etc/locale.conf
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
    locale-gen
}

set_keymap() {
    echo "KEYMAP=$KEYMAP" > /etc/vconsole.conf
}

set_hosts() {
    local hostname="$1"; shift

    cat > /etc/hosts <<EOF
127.0.0.1 localhost.localdomain localhost $hostname
::1       localhost.localdomain localhost $hostname
EOF
}

set_fstab() {    
    genfstab -U /mnt >> /mnt/etc/fstab
}

set_daemons() {
    systemctl enable NetworkManager ntpd
}

set_sudoers() {
    echo "%wheel ALL=(ALL:ALL) ALL" >> /etc/sudoers
}

create_user() {
    local name="$1"; shift
    local password="$1"; shift

    useradd -m -G wheel -p "$(openssl passwd -1 $password)" $name 
}

get_uuid() {
    blkid -o export "$1" | grep UUID | awk -F= '{print $2}'
}

format_filesystems() {
    mkfs.ext4 -F $PART_ROOT
    mkfs.fat -F 32 $PART_BOOT
    mkswap $PART_SWAP
    swapon $PART_SWAP
}

configure_boot() {
    local boot_uuid=$(get_uuid $PART_BOOT)
    bootctl install
    echo "default\tarch.conf\ntimeout\t20\nconsole-mode\tmax\neditor\tno" > /boot/loader/loader.conf
    echo "title\tArch Linux\nlinux\t/vmlinuz-linux\ninitrd\t/initramfs-linux.img\noptions\troot=UUID=$boot_uuid rw" > /boot/loader/entries/arch.conf
}

if [ "$1" == "chroot" ]
then
    configure
else
    setup
fi