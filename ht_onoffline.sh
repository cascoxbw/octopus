#!/bin/bash

STATE="`cat /proc/cpuinfo | awk '/siblings/ {siblings=$3} /cpu cores/{cpucores=$4} END {if(siblings>cpucores){print \"enabled\" } else {print \"disabled\"}}'`"

if [ "$1" = "offline" -a "$STATE" != "enabled" ]; then
	echo "HT is disabled or sibling CPUs are already offlined"
	exit 0
fi

HTPAIRS="`cat /sys/devices/system/cpu/cpu0/topology/thread_siblings_list`"

if [ "$HTPAIRS" = "0-1" ]; then
	echo "Warning: HT pairs are even/odd"
fi

CPUMAX=128

if [ "$1" = "online" ]; then
	echo "Onlining:"
	for((ii=0;ii<$CPUMAX;ii++)); do
		test -e /sys/devices/system/cpu/cpu$ii/online || continue
		echo 1 > /sys/devices/system/cpu/cpu$ii/online
		echo -e "\tCPU $ii"
	done
elif [ "$1" = "offline" ]; then
	if [ "$HTPAIRS" = "0-1" ]; then
		echo "Offlining:"
		for((ii=1;ii<$CPUMAX;ii+=2)); do
			test -e /sys/devices/system/cpu/cpu$ii/online || continue
			echo 0 > /sys/devices/system/cpu/cpu$ii/online
			echo -e "\tCPU $ii"
		done
	else
		MAXCPUNO=0
		for((ii=4;ii<$CPUMAX;ii++)); do
			test -e /sys/devices/system/cpu/cpu$ii/online || continue
			if [ $ii -gt $MAXCPUNO ]; then
				MAXCPUNO=$ii
			fi
		done
		((MAXCPUNO++))
		((MAXCPUNO=MAXCPUNO/2))

		echo "Offlining:"
		for((ii=$MAXCPUNO;ii<$CPUMAX;ii++)); do
			test -e /sys/devices/system/cpu/cpu$ii/online || continue
			echo 0 > /sys/devices/system/cpu/cpu$ii/online
			echo -e "\tCPU $ii"
		done
	fi
else
	echo "Usage: $0 [online | offline]"
	exit 1
fi
