#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ezLNT import Ui_ezLNT
from flashtool_ import Ui_Dialog
from dev_info import Ui_Software
from dev_log import Ui_VersionUpdate
from login_ import Ui_LogIn
import serial
import serial.tools.list_ports
import socket
from os import getenv
import re
import sys
import select
import threading
import datetime
from xlwt import Workbook


class SerialPort(object):
    def __init__(self, portname):
        self.portname = portname
        self.createcom()

    def createcom(self):
        self.com = serial.Serial(baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE, timeout=0.6)

    def opencom(self):
        self.com.port = self.portname
        self.com.open()

    def closecom(self):
        self.com.port = self.portname
        self.com.close()

    def sendcmd(self, cmd):
        self.com.write(bytes(cmd, 'utf-8'))
        self.rsp = self.com.read(400)
        if self.rsp:
            self.rsp2str = self.rsp.decode('utf-8')
        else:
            self.rsp = ' '
            self.rsp2str = self.rsp * 400
        self.com.reset_input_buffer()
        self.com.reset_output_buffer()
        return self.rsp2str

    def state(self):
        return self.com.is_open


def get_local_portlist():
    portlist = []
    ports = list(serial.tools.list_ports.comports())
    if ports is not None:
        for p in ports:
            portlist.append(p[0])
    return portlist


def get_local_ip():
    local_ip = socket.gethostbyname(socket.gethostname())
    return local_ip


@pyqtSlot()
def extract_zb_info(i):
    zb_list = []
    info = globals()['p' + str(i)].sendcmd('i')
    if info.find('Nwk Addr=') != -1:
        pNwk = info.index('Nwk Addr=') + len('Nwk Addr=')
        Nwk = info[pNwk:pNwk + 6]
    else:
        Nwk = 'N/A'
    zb_list.append(Nwk)
    if info.find('Mac Addr=') != -1:
        pMac = info.index('Mac Addr=') + len('Mac Addr=')
        Mac = info[pMac:pMac + 16]
    else:
        Mac = 'N/A'
    zb_list.append(Mac)
    if info.find('Channel=') != -1:
        pCh = info.index('Channel=') + len('Channel=')
        Ch = info[pCh:pCh + 2]
    else:
        Ch = 'N/A'
    zb_list.append(Ch)
    if info.find('Type=') != -1:
        pType = info.index('Type=') + len('Type=')
        Type = info[pType:pType + 20]
    else:
        Type = 'N/A'
    zb_list.append(Type)
    if info.find('Ver=') != -1:
        pVer = info.index('Ver=') + len('Ver=')
        Ver = info[pVer:pVer + 4]
    else:
        Ver = 'N/A'
    zb_list.append(Ver)
    return zb_list


@pyqtSlot()
def extract_zb_rsp(i, chrcmd):
    zb_rsps = []
    if globals()['p' + str(i)].state():
        zb_rsp = globals()['p' + str(i)].sendcmd(chrcmd)
    else:
        zb_rsp = 'port is not open'
    zb_rsps.append(zb_rsp)
    return zb_rsps


@pyqtSlot()
def extract_blm_info(i):
    blm_list = []
    info1 = globals()['p' + str(i)].sendcmd('version\r\n')
    if info1.find('MESH v') != -1:
        pversion = info1.index('MESH v') + len('MESH v')
        version = info1[pversion:pversion + 15]
        blm_ver = version[0:3]
        if version[4:6] == '00':
            blm_type = 'LPN'
        elif version[4:6] == '03':
            blm_type = 'RPN'
        elif version[4:6] == '07':
            blm_type = 'RPFN'
        elif version[4:6] == '01':
            blm_type = 'RN'
        else:
            blm_type = 'PD'
    else:
        blm_ver = 'N/A'
        blm_type = 'N/A'
    blm_list.append(blm_ver)
    blm_list.append(blm_type)

    info2 = globals()['p' + str(i)].sendcmd('nwkAddr\r\n')
    if info2.find('element address') != -1:
        pnwkAddr = info2.index('element address') + len('element address')
        blm_nwk = info2[pnwkAddr:pnwkAddr + 6]
        if blm_nwk == ' 0x00\r':
            blm_st = 'Unprov'
        else:
            blm_st = 'Active'
    else:
        blm_nwk = 'N/A'
        blm_st = 'N/A'
    blm_list.append(blm_nwk)
    blm_list.append(blm_st)
    return blm_list


@pyqtSlot()
def extract_blm_rsp(i, cmd):
    blm_rsps = []
    if globals()['p' + str(i)].state():
        blm_rsp = globals()['p' + str(i)].sendcmd(str(cmd))
    else:
        blm_rsp = 'port is not open'
    blm_rsps.append(blm_rsp)
    return blm_rsps


class CltWorker(QObject):
    skt_clt = pyqtSignal(str)
    skt_clt_data_port = pyqtSignal(str, str)

    def __init__(self, ):
        super(CltWorker, self).__init__()

    def clt_init(self, addr_ip):
        self.clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clt.connect((addr_ip, 50000))
        self.Alive = True
        self.thread_read = threading.Thread(target=self.clt_recving)
        self.thread_read.setDaemon(True)
        self.thread_read.start()
        self.skt_clt.emit('connect to server: ' + str(self.clt.getpeername()))

    def clt_send(self, index, var_data_type):
        if index == 0:
            send_msg = '[text][{0}]'.format(str(var_data_type))
        elif index == 1:
            send_msg = '[name]{0}'.format(str(var_data_type))
        elif index == 2:
            send_msg = '[info]{0}'.format(str(var_data_type))
        elif index == 3:
            send_msg = '[msgs]{0}'.format(str(var_data_type))
        else:
            pass
        self.clt.send(str(send_msg).encode())
        self.skt_clt.emit('send: ' + str(var_data_type))

    def clt_recving(self):
        while self.Alive:
            rcv_msg = self.clt.recv(1024)       # recv buffer
            if not rcv_msg:
                self.clt_close()
                self.skt_clt.emit('server has closed, connection broke')
                break
            else:
                self.clt_handling_data(str(rcv_msg))
        self.Alive = False

    def clt_close(self):
        self.clt.close()
        if self.Alive:
            self.Alive = False

    def clt_handling_data(self, data):
        try:
            parse_head = re.findall(r'\[(.*?)\]', data)
            if parse_head is not None:
                header = parse_head[0]
                if header == 'word':
                    parse_belly = re.findall(r'\[(.*?)\]', data)
                    cmd = parse_belly[1]
                    self.skt_clt.emit('received: ' + str(cmd))
                    if cmd == 'bind':
                        pnl = get_local_portlist()
                        pnl_num = len(pnl)
                        if pnl_num:
                            self.clt_send(1, pnl)
                        else:
                            self.clt_send(0, 'no select port(s) need to operate')
                    elif cmd == 'unbind':
                        self.clt_send(1, None)
                    else:
                        pass
                elif header == 'port':
                    parse_belly = re.findall(r'\[(.*?)\]', data)
                    cmd = parse_belly[1]
                    port_list = parse_belly[2]
                    self.skt_clt.emit('receive: ' + str(cmd) + ' to local port #' + str(port_list))
                    # format_cmd = cmd + '\r\n'
                    self.skt_clt_data_port.emit(str(cmd), port_list)
                else:
                    pass
            else:
                self.skt_clt.emit('error in parsing the data from server.')
                return None
        except Exception as e:
            self.skt_clt.emit('clt_handling_data: ' + repr(e))


class SrvWorker(QObject):
    skt_srv = pyqtSignal(str)
    skt_srv_data_update = pyqtSignal(int, str, list)            # clt_id, clt_ip, state_list
    skt_srv_data_recv = pyqtSignal(int, str, list)

    def __init__(self):
        super(SrvWorker, self).__init__()

    def srv_init(self):
        self.thread_run = threading.Thread(target=self.srv_run)
        self.thread_run.setDaemon(True)
        self.thread_run.start()

    def srv_run(self):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.bind((socket.gethostname(), 50000))
        self.srv.setblocking(False)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.listen(20)
        self.skt_srv.emit(str(self.srv.getsockname()) + ' : wait for connect...')
        self.inputs = [self.srv]
        self.outputs = []
        self.conn_num = 0
        while self.inputs:
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)

            if not (readable or writable or exceptional):
                self.skt_srv.emit(str(self.srv.getsockname()) + ': time out, no client is connecting')
                self.srv_shutdown()
                self.skt_srv.emit('server service closed')
                break

            for s in readable:
                if s is self.srv:
                    connection, clt_addr = s.accept()
                    self.conn_num += 1
                    self.skt_srv.emit('connect success: client #' + str(self.conn_num) + ': ' + str(clt_addr))
                    self.skt_srv_data_update.emit(self.conn_num, str(clt_addr), ['on'])
                    connection.setblocking(False)
                    self.inputs.append(connection)
                else:
                    try:
                        srv_rcv = s.recv(1024)
                        if not srv_rcv:
                            self.skt_srv.emit('receive empty data from ' + str(s.getpeername()))
                            self.skt_srv_data_update.emit(self.conn_num, str(s.getpeername()), ['off'])
                            self.inputs.remove(s)
                            if s in self.outputs:
                                self.outputs.remove(s)
                            s.close()
                        else:
                            self.srv_handling_data(self.conn_num, str(s.getpeername()), srv_rcv.decode())
                            if s not in self.outputs:
                                self.outputs.append(s)
                    except ConnectionResetError:
                        self.skt_srv_data_update.emit(self.conn_num, str(s.getpeername()), ['off'])
                        self.skt_srv.emit('client side closed')
                        self.srv_shutdown()

                    except Exception as e:
                        self.skt_srv.emit('server receive error: ' + repr(e))
                        self.srv_shutdown()

            for s in exceptional:
                self.skt_srv.emit("exception condition on " + str(s.getpeername()))
                self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                s.close()
                break

    def srv_handling_data(self, clt_id, clt_ip, data):
        try:
            parse_head = re.findall(r'\[(.*?)\]', data)
            if parse_head is not None:
                header = parse_head[0]
                if header == 'text':
                    parse_belly = re.findall(r'\[(.*?)\]', data)
                    self.skt_srv_data_recv.emit(clt_id, 'text', parse_belly)
                elif header == 'name':
                    parse_belly = re.findall(r'\'(.*?)\'', data)
                    self.skt_srv_data_recv.emit(clt_id, 'name', parse_belly)
                elif header == 'info':
                    parse_belly = re.findall(r'\'(.*?)\'', data)
                    self.skt_srv_data_recv.emit(clt_id, 'info', parse_belly)
                elif header == 'msgs':
                    parse_belly = re.findall(r'\[(.*?)\]', data)
                    self.skt_srv_data_recv.emit(clt_id, 'msgs', parse_belly)
                else:
                    pass
            else:
                self.skt_srv.emit('error in parsing the data from #' + str(clt_id) + ': ' + str(clt_ip))
                return None
        except Exception as e:
            self.skt_srv.emit('srv_handling_data: ' + repr(e))

    def srv_broadcast_msg(self, bc_msg):
        for inpt in self.inputs:
            if inpt != self.srv:
                inpt.send(str(bc_msg).encode())
                self.skt_srv.emit('broadcast ' + str(inpt.getpeername()) + ': ' + str(bc_msg))

    def srv_unicast_msg(self, index, uc_msg):
        self.inputs[index].send(str(uc_msg).encode())
        self.skt_srv.emit('unicast ' + str(self.inputs[index].getpeername()) + ': ' + str(uc_msg))

    def srv_send_format(self, index, msg, lst):
        if index == 0:
            process_msg = '[word][{0}]{1}'.format(str(msg), None)
        elif index == 1:
            process_msg = '[port][{0}]{1}'.format(str(msg), str(lst))
        else:
            pass
        return process_msg

    def srv_shutdown(self):
        try:
            for inpt in self.inputs:
                inpt.close()
            for oupt in self.outputs:
                oupt.close()
            self.srv.close()
            self.srv.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        except Exception as e:
            self.skt_srv.emit('srv_shutdown: ' + repr(e))


class ProgramDlg(Ui_Dialog, QDialog):
    def __init__(self):
        super(ProgramDlg, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Flash Program')
        self.btnFlDlg.clicked.connect(self.open_file_dlg)
        self.btnProgram.clicked.connect(self.start_program)

    def open_file_dlg(self):
        fw = QFileDialog.getOpenFileName(self, 'Select Firmware', '', 'Binary Files(*.bin)')
        if fw:
            fw_name = fw[0]
        else:
            fw_name = ''
        self.lineFl.setText(str(fw_name))

    def check_program_opt(self):
        if self.cbErsEPROM.isChecked() and self.cbVrfy.isChecked():
            hint = 'Erase eeprom and Verify'
        elif self.cbVrfy.isChecked() and not self.cbErsEPROM.isChecked():
            hint = 'Verify and not Erase eeprom'
        elif self.cbErsEPROM.isChecked() and not self.cbVrfy.isChecked():
            hint = 'Erase eeprom and not Verify'
        else:
            hint = 'not Erase eeprom and not Verify'
        return hint

    def start_program(self, opt):
        pass
        # l = ftd2xx.listDevices()
        # f = ftd2xx.getDeviceInfoDetail(0, True)
        # print(l, f)


class Software(Ui_Software, QDialog):
    def __init__(self):
        super(Software, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Software')
        self.set_content()

    def set_content(self):
        self.labelInfo.setText('Any Question, Send E-mail to chan.luo@nxp.com')
        self.labelLogo.setText('ezLNT Test Software')


class Version(Ui_VersionUpdate, QDialog):
    def __init__(self):
        super(Version, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Version Update')
        self.set_content()

    def set_content(self):
        self.labelVersion.setText('ver 1.0.1')
        self.labelUpdateFeature.setText('1. Add some features.\n'
                                        '2. Fix some bugs.')


class ZbWorker(QObject):
    sig_zb = pyqtSignal(int, list)

    def __init__(self, idx, cc):
        super(ZbWorker, self).__init__()
        self.index = idx
        self.cmd = cc

    @pyqtSlot()
    def work_zb_getinfo(self):
        zb_inflst = extract_zb_info(self.index)
        self.sig_zb.emit(self.index, zb_inflst)
        app.processEvents()

    @pyqtSlot()
    def work_zb_getrsp(self):
        zb_rsps = extract_zb_rsp(self.index, self.cmd)
        self.sig_zb.emit(self.index, zb_rsps)
        app.processEvents()

    @pyqtSlot()
    def abort(self):
        self.quit()


class BlmWorker(QObject):
    sig_blm = pyqtSignal(int, list)

    def __init__(self, idx, cc):
        super(BlmWorker, self).__init__()
        self.index = idx
        self.cmd = cc

    @pyqtSlot()
    def work_blm_getinfo(self):
        blm_inflst = extract_blm_info(self.index)
        self.sig_blm.emit(self.index, blm_inflst)
        app.processEvents()

    @pyqtSlot()
    def work_blm_getrsp(self):
        blm_rsps = extract_blm_rsp(self.index, self.cmd)
        self.sig_blm.emit(self.index, blm_rsps)
        app.processEvents()

    @pyqtSlot()
    def abort(self):
        self.quit()


class LogWindow(Ui_LogIn, QMainWindow):
    def __init__(self):
        super(LogWindow, self).__init__()
        self.setupUi(self)
        self.lblLoginUserName.setText(str(getenv('USERNAME')))
        self.rbLoginSelZb.clicked.connect(self.enter_sel_mode)
        self.rbLoginSelBlm.clicked.connect(self.enter_sel_mode)

    def enter_sel_mode(self):
        if self.rbLoginSelZb.isChecked():
            ui.gen_check_mode(0)
        elif self.rbLoginSelBlm.isChecked():
            ui.gen_check_mode(1)
        ui.show()
        self.close()


class ezLNTDemo(Ui_ezLNT, QMainWindow):
    def __init__(self):
        super(ezLNTDemo, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('ezLNT')

        self.zb_selist = []                             # select list, [port_id, clt_id]
        self.blm_selist = []                            # select list, [port_id, clt_id]

        self.threads = []                               # save for port-option thread

        self.zb_num = 0                                 # local zb port number
        self.blm_num = 0                                # local ble mesh port number

        self.num_sum = []                               # zb/blm number list
        self.num_head = []
        self.num_toe = []                               # clients save index format

        self.table = QTableWidget()                     # data-table to display info
        self.table_data_lines = []                      # for data-table selection
        self.clients_info = []                          # for id/ip on client
        self.clients = []

        self.socket_list = []                           # socket use
        self.socket_cmd = ''                            # socket use

        self.clients_save_contents = []
        self.rsps = []

        self.OptModeFlag = 0                            # 0 for zb, 1 for ble mesh, 2 for thread

        self.xls_file = Workbook(encoding='utf-8')      # for table data saved in .xls

        self.btnGenLog.clicked.connect(self.event_GenLog)
        self.btnGenClear.clicked.connect(self.event_GenCln)
        self.btnGenSelect.clicked.connect(self.event_GenSelect)
        self.btnGenSend.clicked.connect(self.event_GenSend)
        self.cbGenAll.stateChanged.connect(self.gen_select_all_ports)

        self.actionExit.triggered.connect(self.gen_exit)
        self.actionRefresh.triggered.connect(self.gen_refresh)
        self.actionSoftware.triggered.connect(self.gen_software)
        self.actionVersion.triggered.connect(self.gen_version)
        self.actionDumpInfo.triggered.connect(self.gen_dump_info)

        # zigbee
        self.zbShowInfo.clicked.connect(self.event_zbShowInfo)
        self.zbToggle.clicked.connect(self.event_zbToggle)
        self.zbRunScript.clicked.connect(self.event_zbRunScpt)
        self.zbLoadConfig.clicked.connect(self.event_zbLdCfg)
        self.zbSaveConfig.clicked.connect(self.event_zbSvCfg)
        self.zbProgram.clicked.connect(self.event_zbProgram)

        # ble mesh
        self.blmToggle.clicked.connect(self.event_blmToggle)
        self.blmReset.clicked.connect(self.event_blmReset)
        self.blmFN.clicked.connect(self.event_blmFN)
        self.blmRefresh.clicked.connect(self.event_blmRefresh)
        self.blmRunScpt.clicked.connect(self.event_blmRunScpt)
        self.blmProgram.clicked.connect(self.event_blmProgram)
        self.blmView.clicked.connect(self.event_blmView)

        self.rbSetClient.clicked.connect(self.set_socket_mode)
        self.rbSetServer.clicked.connect(self.set_socket_mode)
        self.btnClientSwitch.clicked.connect(self.skt_clt_event)
        self.btnClientSend.clicked.connect(self.skt_cltsend)
        self.btnServerSwitch.clicked.connect(self.skt_srv_event)
        self.btnServerSend.clicked.connect(self.skt_srvsend)

    def gen_check_mode(self, mode):
        self.table_data_lines.clear()
        self.clients_info = []

        self.zb_selist.clear()
        self.blm_selist.clear()

        self.threads = []

        self.zb_num = 0
        self.blm_num = 0

        self.num_sum = []
        self.num_head = []
        self.num_toe = []

        self.OptModeFlag = 0

        lpl = get_local_portlist()
        if mode == 0:
            self.OptModeFlag = 0
            self.tw.setCurrentIndex(0)
            self.tw.setTabEnabled(1, False)
            self.zb_num = len(lpl)

            self.num_sum.append(self.zb_num)
            self.num_head.append(0)
            self.num_toe.append(self.zb_num)

            self.set_zb_table_format()
            self.set_table_number(self.zb_num)

            self.set_socket_btn(2, False)
            self.sb.showMessage(str(self.zb_num) + ' port(s) found in PC.')

            if self.zb_num > 0:
                for n in range(self.zb_num):
                    com_name = 'p' + str(n)
                    globals()[com_name] = SerialPort(lpl[n])
                    self.zb_selist.append([n, 0])
                self.show_portname(self.zb_num, lpl, 0, 'local')
                # self.btnGenSelect.setEnabled(True)
                self.set_mode_btn_state(self.OptModeFlag, True)
            else:
                # self.btnGenSelect.setEnabled(False)
                self.set_mode_btn_state(self.OptModeFlag, False)

        elif mode == 1:
            self.OptModeFlag = 1
            self.tw.setCurrentIndex(1)
            self.tw.setTabEnabled(0, False)
            self.blm_num = len(lpl)

            self.num_sum.append(self.blm_num)
            self.num_head.append(0)
            self.num_toe.append(self.blm_num)

            self.set_blm_table_format()
            self.set_table_number(self.blm_num)

            self.set_socket_btn(2, False)
            self.sb.showMessage(str(self.blm_num) + ' port(s) found in PC.')

            if self.blm_num > 0:
                for n in range(self.blm_num):
                    com_name = 'p' + str(n)
                    globals()[com_name] = SerialPort(lpl[n])
                    self.blm_selist.append([n, 0])
                self.show_portname(self.blm_num, lpl, 0, 'local')
                # self.btnGenSelect.setEnabled(True)
                self.set_mode_btn_state(self.OptModeFlag, True)
            else:
                # self.btnGenSelect.setEnabled(False)
                self.set_mode_btn_state(self.OptModeFlag, False)
        else:
            pass

    def set_socket_mode(self):
        if self.rbSetClient.isChecked():

            self.set_socket_btn(0, True)
            self.set_socket_btn(1, False)

            if self.lblServerAddr:
                self.lblServerAddr.clear()

            self.cltwkr = CltWorker()
            self.cltwkr.skt_clt.connect(self.socket_log_print)
            self.cltwkr.skt_clt_data_port.connect(self.event_HandlePortCmd)

        elif self.rbSetServer.isChecked():

            self.set_socket_btn(0, False)
            self.set_socket_btn(1, True)

            self.lblServerAddr.setText(str(get_local_ip()))

            self.srvwkr = SrvWorker()
            self.srvwkr.skt_srv.connect(self.socket_log_print)
            self.srvwkr.skt_srv_data_update.connect(self.event_UpdateSrvData)
            self.srvwkr.skt_srv_data_recv.connect(self.event_HandleSrvRsp)
        else:
            pass

    def event_UpdateSrvData(self, clt_id, clt_ip, state):
        try:
            if state[0] == 'on':
                self.cbTargetClientAddr.addItem(str(clt_ip))
                if [clt_id, str(clt_ip)] not in self.clients_info:
                    self.clients_info.append([clt_id, str(clt_ip)])
            elif state[0] == 'off':
                self.cbTargetClientAddr.removeItem(clt_id+1)
                if [clt_id, str(clt_ip)] in self.clients_info:
                    self.clients_info.remove([clt_id, str(clt_ip)])
            else:
                pass
            # self.tbCLLog.append('clients_info: ' + str(self.clients_info))
        except Exception as e:
            self.tbCLLog.append('event_UpdateSrvData: ' + repr(e))

    def event_HandleSrvRsp(self, clt_id, string, data_list):
        try:
            if string == 'text':

                self.tbCLLog.append('receive: ' + str(data_list[1]) + ' from #' + str(clt_id))

            elif string == 'name':

                if clt_id not in self.clients:
                    self.clients.append(clt_id)
                    self.num_sum.append(len(data_list))

                    port_sum = 0
                    for ns in self.num_sum:
                        port_sum += ns
                    self.sb.showMessage(str(port_sum) + ' port(s) found in PC.')

                    self.num_head.append(self.num_toe[clt_id-1])
                    self.num_toe.append(self.num_head[clt_id] + len(data_list))

                    for num in range(self.num_head[clt_id], self.num_toe[clt_id]):
                        self.table_row_pos = self.table.rowCount()
                        self.table.insertRow(self.table_row_pos)
                        self.show_remote_portname(num, num-self.num_head[clt_id], data_list, clt_id)

            elif string == 'info':
                self.tbCLLog.append('info datalist length: ' + str(len(data_list)))

                for num in range(self.num_head[clt_id], self.num_toe[clt_id]):
                    if num-self.num_toe[clt_id-1] in [bs[0] for bs in self.blm_selist]:

                        if len(data_list) == 5:
                            self.set_zb_datas(num, data_list)
                        elif len(data_list) == 4:
                            self.set_blm_datas(num, data_list)
                        else:
                            pass
                    else:
                        pass

            elif string == 'msgs':
                self.tbOutText.appendPlainText('client #' + str(clt_id) + ': ')

                for dl in data_list:
                    format_dl = dl.replace('\r', ' ').replace('\n', ' ')
                    self.tbOutText.appendPlainText(str(format_dl))
            else:
                pass

        except Exception as e:
            self.tbCLLog.append('event_HandleSrvRsp: ' + repr(e))

    def set_mode_btn_state(self, num, state):
        if num == 0:
            self.zbShowInfo.setEnabled(state)
            self.zbToggle.setEnabled(state)
            self.zbRunScript.setEnabled(state)
            self.zbLoadConfig.setEnabled(state)
            self.zbSaveConfig.setEnabled(state)
            self.zbProgram.setEnabled(state)
        elif num == 1:
            self.blmToggle.setEnabled(state)
            self.blmReset.setEnabled(state)
            self.blmFN.setEnabled(state)
            self.blmRefresh.setEnabled(state)
            self.blmRunScpt.setEnabled(state)
            self.blmProgram.setEnabled(state)
            self.blmView.setEnabled(state)
        else:
            pass

    def set_socket_btn(self, num, state):
        if num == 0:
            self.btnClientSwitch.setEnabled(state)
            self.btnClientSend.setEnabled(state)
        elif num == 1:
            self.btnServerSwitch.setEnabled(state)
            self.btnServerSend.setEnabled(state)
        else:
            self.btnClientSwitch.setEnabled(state)
            self.btnClientSend.setEnabled(state)
            self.btnServerSwitch.setEnabled(state)
            self.btnServerSend.setEnabled(state)

    def event_zbShowInfo(self):
        if not self.zbToggle.isChecked():
            self.msg = QMessageBox.information(self, 'Error', 'Please open port(s) first then query info.')
        else:
            for zs in self.zb_selist:
                self.wkr1 = ZbWorker(zs[0], None)
                self.thd1 = QThread()
                self.threads.append((self.thd1, self.wkr1))
                self.wkr1.sig_zb.connect(self.display_zb_log)
                self.wkr1.moveToThread(self.thd1)
                self.thd1.started.connect(self.wkr1.work_zb_getinfo)
                self.thd1.start()

    def display_zb_log(self, i, lst):
        try:
            self.set_zb_datas(i, lst)
            self.tbCLLog.append('GetInfo : thread for #' + str(i + 1) + ' port is in process...')
        except Exception as e:
            self.tbCLLog.append('display_zb_log: ' + repr(e))

    def set_zb_datas(self, index, lst):
        self.zb_nwk = QTableWidgetItem(str(lst[0]))
        self.zb_nwk.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 4, self.zb_nwk)

        self.zb_mac = QTableWidgetItem(str(lst[1]))
        self.zb_mac.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 3, self.zb_mac)

        self.zb_ch = QTableWidgetItem(str(lst[2]))
        self.zb_ch.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 5, self.zb_ch)

        self.zb_type = QTableWidgetItem(str(lst[3]))
        self.zb_type.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 6, self.zb_type)

        self.zb_ver = QTableWidgetItem(str(lst[4]))
        self.zb_ver.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 7, self.zb_ver)

    def set_blm_datas(self, index, lst):
        self.blm_ver = QTableWidgetItem(str(lst[0]))
        self.blm_ver.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 5, self.blm_ver)

        self.blm_type = QTableWidgetItem(str(lst[1]))
        self.blm_type.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 4, self.blm_type)

        self.blm_nwk = QTableWidgetItem(str(lst[2]))
        self.blm_nwk.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 3, self.blm_nwk)

        self.blm_st = QTableWidgetItem(str(lst[3]))
        self.blm_st.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 6, self.blm_st)

    def display_blm_log(self, i, lst):
        try:
            self.set_blm_datas(i, lst)
            self.tbCLLog.append('GetInfo : thread for #' + str(i + 1) + ' port is in process...')
        except Exception as e:
            self.tbCLLog.append('display_blm_log: ' + repr(e))

    def gen_select_all_ports(self):
        for line in self.table_data_lines:
            if self.cbGenAll.isChecked():
                line[1].setChecked(True)
            else:
                line[1].setChecked(False)

    def set_table_number(self, n):
        self.table.setRowCount(n)
        self.tblLayout.addWidget(self.table)

    def set_zb_table_format(self):
        self.table.setGeometry(QRect(10, 220, 1031, 600))
        self.table.setMinimumSize(QSize(1000, 600))
        self.table.setLineWidth(38)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ['', 'COM', 'IP', 'IEEE/MAC', 'NwkAddr', 'Ch.', 'Type', 'Ver.', 'Response', 'Program'])
        self.tbl_font = QFont()
        self.tbl_font.setBold(True)
        self.table.horizontalHeader().setFont(self.tbl_font)
        self.table.horizontalHeader().setStyleSheet('QHeaderView::section{background:lightgray}')
        self.table.horizontalHeader().resizeSection(0, 50)
        self.table.horizontalHeader().resizeSection(1, 90)
        self.table.horizontalHeader().resizeSection(2, 190)
        self.table.horizontalHeader().resizeSection(3, 190)
        self.table.horizontalHeader().resizeSection(4, 100)
        self.table.horizontalHeader().resizeSection(5, 50)
        self.table.horizontalHeader().resizeSection(6, 160)
        self.table.horizontalHeader().resizeSection(7, 60)
        self.table.horizontalHeader().resizeSection(8, 155)
        self.table.horizontalHeader().resizeSection(9, 145)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.installEventFilter(self)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.tblLayout.addWidget(self.table)

    def set_blm_table_format(self):
        self.table.setGeometry(QRect(10, 220, 1031, 600))
        self.table.setMinimumSize(QSize(1000, 600))
        self.table.setLineWidth(38)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ['', 'COM', 'IP', 'NwkAddr', 'Type', 'Ver.', 'St.', 'Response', 'Program'])
        self.tbl_font = QFont()
        self.tbl_font.setBold(True)
        self.table.horizontalHeader().setFont(self.tbl_font)
        self.table.horizontalHeader().setStyleSheet('QHeaderView::section{background:lightgray}')
        self.table.horizontalHeader().resizeSection(0, 50)
        self.table.horizontalHeader().resizeSection(1, 90)
        self.table.horizontalHeader().resizeSection(2, 190)
        self.table.horizontalHeader().resizeSection(3, 100)
        self.table.horizontalHeader().resizeSection(4, 90)
        self.table.horizontalHeader().resizeSection(5, 90)
        self.table.horizontalHeader().resizeSection(6, 90)
        self.table.horizontalHeader().resizeSection(7, 155)
        self.table.horizontalHeader().resizeSection(8, 145)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.installEventFilter(self)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.tblLayout.addWidget(self.table)

    def event_blmToggle(self):
        if not self.blm_selist:
            self.blmToggle.setChecked(False)
            self.msg = QMessageBox.information(self, 'Error', 'No port needs to open.')
        else:
            self.pbGen.setMaximum(len(self.blm_selist))
            if self.blmToggle.isChecked():
                self.blmToggle.setText('Close Port')
                for bs in self.blm_selist:
                    try:
                        if not globals()['p' + str(bs[0])].state():
                            globals()['p' + str(bs[0])].opencom()
                            self.pbGen.setValue(bs[0] + 1)
                            self.set_opt_rsp(bs[0], 'Open', 0)
                    except Exception as e:
                        self.tbCLLog.append('blm_open: ' + repr(e))
                        self.set_opt_rsp(bs[0], 'Access Deny', 1)
            else:
                self.blmToggle.setText('Open Port')
                for bs in self.blm_selist:
                    try:
                        if globals()['p' + str(bs[0])].state():
                            globals()['p' + str(bs[0])].closecom()
                            self.pbGen.setValue(bs[0] + 1)
                            self.set_opt_rsp(bs[0], 'Close', 0)
                    except Exception as e:
                        self.tbCLLog.append('blm_close: ' + repr(e))
                        self.set_opt_rsp(bs[0], 'Access Deny', 1)

    def event_zbToggle(self):
        if not self.zb_selist:
            self.zbToggle.setChecked(False)
            self.msg = QMessageBox.information(self, 'Error', 'No port needs to open.')
        else:
            self.pbGen.setMaximum(len(self.zb_selist))
            if self.zbToggle.isChecked():
                self.zbToggle.setText('Close Port')
                for zs in self.zb_selist:
                    try:
                        if not globals()['p'+str(zs[0])].state():
                            globals()['p'+str(zs[0])].opencom()
                            self.pbGen.setValue(zs[0] + 1)
                            self.set_opt_rsp(zs[0], 'Open', 0)
                    except Exception as e:
                        self.tbCLLog.append('zb_open: ' + repr(e))
                        self.set_opt_rsp(zs[0], 'Access Deny', 1)
            else:
                self.zbToggle.setText('Open Port')
                for zs in self.zb_selist:
                    try:
                        if globals()['p'+str(zs[0])].state():
                            globals()['p'+str(zs[0])].closecom()
                            self.pbGen.setValue(zs[0] + 1)
                            self.set_opt_rsp(zs[0], 'Close', 0)
                    except Exception as e:
                        self.tbCLLog.append('zb_close: ' + repr(e))
                        self.set_opt_rsp(zs[0], 'Access Deny', 1)

    def event_zbHandleCltCmd(self):
        try:
            self.rsps.clear()
            self.clients_save_contents.clear()
            if not self.zbToggle.isChecked():
                self.msg = QMessageBox.information(self, 'Error', 'server requests to open all port.')
                self.cltwkr.clt_send(0, 'wait for clients to open all serial port.')
            else:
                for sl in self.socket_list:
                    self.wkr2 = ZbWorker(sl, self.socket_cmd)
                    self.thd2 = QThread()
                    self.threads.append((self.thd2, self.wkr2))
                    self.wkr2.sig_zb.connect(self.msgs_save)
                    self.wkr2.moveToThread(self.thd2)
                    self.thd2.started.connect(self.wkr2.work_zb_getrsp)
                    self.thd2.start()
        except Exception as e:
            self.tbCLLog.append('event_zbHandleCltCmd: ' + repr(e))

    def event_blmHandleCltCmd(self):
        try:
            self.rsps.clear()
            self.clients_save_contents.clear()
            if not self.blmToggle.isChecked():
                self.msg = QMessageBox.information(self, 'Error', 'server requests to open all port.')
                self.cltwkr.clt_send(0, 'wait for clients to open all serial port.')
            else:
                socket_cmd = self.socket_cmd + '\r\n'
                for sl in self.socket_list:
                    self.wkr0 = BlmWorker(sl, str(socket_cmd))
                    self.thd0 = QThread()
                    self.threads.append((self.thd0, self.wkr0))
                    self.wkr0.sig_blm.connect(self.msgs_save)
                    self.wkr0.moveToThread(self.thd0)
                    self.thd0.started.connect(self.wkr0.work_blm_getrsp)
                    self.thd0.start()
        except Exception as e:
            self.tbCLLog.append('event_blmHandleCltCmd: ' + repr(e))

    def event_blmHandleCltPort(self):
        try:
            self.rsps.clear()
            self.clients_save_contents.clear()
            if not self.blmToggle.isChecked():
                self.msg = QMessageBox.information(self, 'Error', 'server requests to open all port.')
                self.cltwkr.clt_send(0, 'wait for clients to open all serial port.')
            else:
                for sl in self.socket_list:
                    self.wkr4 = BlmWorker(sl, None)
                    self.thd4 = QThread()
                    self.threads.append((self.thd4, self.wkr4))
                    self.wkr4.sig_blm.connect(self.info_save)
                    self.wkr4.moveToThread(self.thd4)
                    self.thd4.started.connect(self.wkr4.work_blm_getinfo)
                    self.thd4.start()
        except Exception as e:
            self.tbCLLog.append('event_blmHandleCltPort: ' + repr(e))

    def event_zbHandleCltPort(self):
        try:
            self.rsps.clear()
            self.clients_save_contents.clear()
            if not self.zbToggle.isChecked():
                self.msg = QMessageBox.information(self, 'Error', 'server requests to open all port.')
                self.cltwkr.clt_send(0, 'wait for clients to open all serial port.')
            else:
                for sl in self.socket_list:
                    self.wkr9 = ZbWorker(sl, None)
                    self.thd9 = QThread()
                    self.threads.append((self.thd9, self.wkr9))
                    self.wkr9.sig_zb.connect(self.info_save)
                    self.wkr9.moveToThread(self.thd9)
                    self.thd9.started.connect(self.wkr9.work_zb_getinfo)
                    self.thd9.start()
        except Exception as e:
            self.tbCLLog.append('event_zbHandleCltPort: ' + repr(e))

    def event_HandlePortCmd(self, cmd, pil):
        try:
            self.socket_cmd = str(cmd)
            self.socket_list = pil.split(', ')
            if self.OptModeFlag == 0:
                if self.socket_cmd == '!':
                    self.event_zbHandleCltPort()
                else:
                    self.event_zbHandleCltCmd()
            elif self.OptModeFlag == 1:
                if self.socket_cmd == 'st':
                    self.event_blmHandleCltPort()
                else:
                    self.event_blmHandleCltCmd()
            else:
                pass
        except Exception as e:
            self.tbCLLog.append('event_HandlePortCmd: ' + repr(e))

    def event_blmReset(self):
        if not self.blmToggle.isChecked():
            self.msg = QMessageBox.information(self, 'Error', 'need open selected port(s) first.')
        else:
            for bs in self.blm_selist:
                self.wkr7 = BlmWorker(bs[0], 'reset\r\n')
                self.thd7 = QThread()
                self.threads.append((self.thd7, self.wkr7))
                self.wkr7.sig_blm.connect(self.local_print)
                self.wkr7.moveToThread(self.thd7)
                self.thd7.started.connect(self.wkr7.work_blm_getrsp)
                self.thd7.start()
                self.tbCLLog.append('factoryReset : thread for #' + str(bs[0]+1) + ' port is in process...')

    def remote_print(self, i, blm_rsps):
        try:
            self.tbOutText.appendPlainText(str(i+1) + ' ' + str(globals()['p' + str(i)].portname))
            self.tbOutText.appendPlainText(''.join(blm_rsps))
        except Exception as e:
            self.tbOutText.appendPlainText('remote_print: ' + repr(e))

    def info_save(self, i, rsp):            # send [info]
        try:
            self.clients_save_contents.append(rsp)
            self.cltwkr.clt_send(2, self.clients_save_contents[0])
        except Exception as e:
            self.tbCLLog.append('info_save: ' + repr(e))

    def msgs_save(self, i, rsp):            # send [msgs]
        try:
            self.rsps.append(rsp)
            self.cltwkr.clt_send(3, self.rsps[0])
        except Exception as e:
            self.tbCLLog.append('msgs_save: ' + repr(e))

    def event_blmFN(self):
        if not self.blmToggle.isChecked():
            self.msg = QMessageBox.information(self, 'Error', 'need open selected port(s) first.')
        else:
            # self.pbGen.setMaximum(len(self.blm_selist))
            for bs in self.blm_selist:
                self.wkr8 = BlmWorker(bs[0], 'factoryReset\r\n')
                self.thd8 = QThread()
                self.threads.append((self.thd8, self.wkr8))
                self.wkr8.sig_blm.connect(self.local_print)
                self.wkr8.moveToThread(self.thd8)
                self.thd8.started.connect(self.wkr8.work_blm_getrsp)
                self.thd8.start()
                self.tbCLLog.append('factoryReset : thread for #' + str(bs[0]+1) + ' port is in process...')

    def event_blmRefresh(self):
        if not self.blmToggle.isChecked():
            self.msg = QMessageBox.information(self, 'Error', 'need open selected port(s) first.')
        else:
            for bs in self.blm_selist:
                self.wkr6 = BlmWorker(bs[0], None)
                self.thd6 = QThread()
                self.threads.append((self.thd6, self.wkr6))
                self.wkr6.sig_blm.connect(self.display_blm_log)
                self.wkr6.moveToThread(self.thd6)
                self.thd6.started.connect(self.wkr6.work_blm_getinfo)
                self.thd6.start()

    def event_blmRunScpt(self):
        self.msg = QMessageBox.information(self, 'Notice', 'Unimplemented function.')

    def event_blmProgram(self):
        self.pd2 = ProgramDlg()
        self.pd2.exec_()

    def event_blmView(self):
        if not self.blmToggle.isChecked():
            self.msg = QMessageBox.information(self, 'Error', 'Please open port(s) first then query info.')
        else:
            for bs in self.blm_selist:
                self.wkr5 = BlmWorker(bs[0], None)
                self.thd5 = QThread()
                self.threads.append((self.thd5, self.wkr5))
                self.wkr5.sig_blm.connect(self.display_blm_log)
                self.wkr5.moveToThread(self.thd5)
                self.thd5.started.connect(self.wkr5.work_blm_getinfo)
                self.thd5.start()

    def skt_clt_event(self):
        self.addr = self.lineServerAddr.text()
        if self.addr:
            if re.match(r'(^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$)', self.addr) is not None:
                if self.btnClientSwitch.isChecked():
                    try:
                        self.cltwkr.clt_init(self.addr)
                        self.btnClientSwitch.setText('Disconn')
                    except AttributeError:
                        pass
                    except ConnectionRefusedError:
                        self.tbCLLog.append('no server could approach')
                    except Exception as e:
                        self.tbCLLog.append('skt_clt_event_connect: ' + repr(e))
                else:
                    answer = QMessageBox.information(self, 'warning', 'sure to close the client connection?',
                                                     QMessageBox.Yes | QMessageBox.No)
                    if answer == QMessageBox.Yes:
                        try:
                            self.cltwkr.clt_close()
                            self.btnClientSwitch.setText('Connect')
                        except AttributeError:
                            pass
                        except Exception as e:
                            self.tbCLLog.append('skt_clt_event_disconn: ' + repr(e))
                    else:
                        pass
            else:
                self.msg = QMessageBox.information(self, 'error', 'invalid server address')
                self.btnClientSwitch.setChecked(False)

        else:
            self.msg = QMessageBox.information(self, 'error', 'invalid address')
            self.btnClientSwitch.setChecked(False)

    def skt_srv_event(self):
        if self.btnServerSwitch.isChecked():
            try:
                self.srvwkr.srv_init()
                self.btnServerSwitch.setText('Terminate')
            except Exception as e:
                self.tbCLLog.append('skt_srv_event_terminate: ' + repr(e))
        else:
            answer = QMessageBox.information(self, 'warning', 'sure to close the server connection?',
                                             QMessageBox.Yes | QMessageBox.No)
            if answer == QMessageBox.Yes:
                try:
                    self.srvwkr.srv_shutdown()
                    self.btnServerSwitch.setText('Setup')
                except OSError:
                    pass
                    # self.tbCLLog.append(' ')
                except Exception as e:
                    self.tbCLLog.append('skt_srv_event_setup: ' + repr(e))
            else:
                pass

    def skt_cltsend(self):
        try:
            msg = self.lineClientCmd.text()
            self.cltwkr.clt_send(0, msg)
        except AttributeError:
            self.tbCLLog.append('no command needs to send.')
        except Exception as e:
            self.tbCLLog.append('skt_cltsend: ' + repr(e))

    def skt_srvsend(self):
        try:
            self.cmd = self.lineServerCmd.text()
            index = self.cbTargetClientAddr.currentIndex()
            if index == 0:
                send_msg = self.srvwkr.srv_send_format(0, str(self.cmd), None)
                self.srvwkr.srv_broadcast_msg(send_msg)
            elif index == 1:
                if self.OptModeFlag == 0:
                    zs_lst = [zs[0] for zs in self.zb_selist]
                    self.tbCLLog.append('selected ports: ' + str(zs_lst))
                    send_msg = self.srvwkr.srv_send_format(1, str(self.cmd), zs_lst)
                    for zs in self.zb_selist:
                        if zs[1] == 0:
                            continue
                        self.srvwkr.srv_unicast_msg(zs[1], send_msg)
                elif self.OptModeFlag == 1:
                    bs_lst = [bs[0] for bs in self.blm_selist]
                    self.tbCLLog.append('selected ports: ' + str(bs_lst))
                    send_msg = self.srvwkr.srv_send_format(1, str(self.cmd), bs_lst)
                    for bs in self.blm_selist:
                        if bs[1] == 0:
                            continue
                        self.srvwkr.srv_unicast_msg(bs[1], send_msg)
            else:
                send_msg = self.srvwkr.srv_send_format(0, str(self.cmd), None)
                self.srvwkr.srv_unicast_msg(index-1, send_msg)

        except AttributeError:
            self.tbCLLog.append('no cmd needs to send.')
        except Exception as e:
            self.tbCLLog.append('skt_srvsend: ' + repr(e))

    def socket_log_print(self, strr):
        self.tbCLLog.append(str(strr))

    def gen_exit(self):
        qApp.quit()

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.table:
            self.contx_menu = QMenu(self)
            local_port_cmd = self.contx_menu.addAction('Select to send command')
            if self.contx_menu.exec_(event.globalPos()) == local_port_cmd:
                cur_row = self.table.currentRow()
                if cur_row is not None:
                    cmd, sta = QInputDialog.getText(self, 'input', 'input command:')
                    if sta:
                        self.single_send(cur_row, cmd)
                return True
        return super(ezLNTDemo, self).eventFilter(source, event)

    def gen_dump_info(self):
        try:
            self.current_time = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
            self.tabl = self.file.add_sheet(str(self.current_time))

            if self.OptModeFlag == 0:
                num = self.zb_num
            elif self.OptModeFlag == 1:
                num = self.blm_num
            else:
                pass
            for i in range(num):
                if self.table.item(i, 1) is not None:
                    self.tabl.write(i, 1, self.table.item(i, 1).text())
                else:
                    self.tabl.write(i, 1, 'N/A')
                if self.table.item(i, 2) is not None:
                    self.tabl.write(i, 2, self.table.item(i, 2).text())
                else:
                    self.tabl.write(i, 2, 'N/A')
                if self.table.item(i, 3) is not None:
                    self.tabl.write(i, 3, self.table.item(i, 3).text())
                else:
                    self.tabl.write(i, 3, 'N/A')
                if self.table.item(i, 4) is not None:
                    self.tabl.write(i, 4, self.table.item(i, 4).text())
                else:
                    self.tabl.write(i, 4, 'N/A')
                if self.table.item(i, 5) is not None:
                    self.tabl.write(i, 5, self.table.item(i, 5).text())
                else:
                    self.tabl.write(i, 5, 'N/A')
                if self.table.item(i, 6) is not None:
                    self.tabl.write(i, 6, self.table.item(i, 6).text())
                else:
                    self.tabl.write(i, 6, 'N/A')
            self.file.save('ezLNT_portinfo.xls')
            self.tbCLLog.append('Dump port info in current dir.')
        except Exception as e:
            self.tbCLLog.append('gen_dump_info: ' + repr(e))

    def gen_refresh(self):
        if self.zbToggle.isChecked() or self.blmToggle.isChecked():
            self.msg = QMessageBox.information(self, 'Error', 'Please close port first and refresh.')
        else:
            self.zb_num = 0
            self.zb_selist.clear()

            self.blm_num = 0
            self.blm_selist.clear()

            self.table_data_lines.clear()
            self.num_sum.clear()
            self.num_head.clear()
            self.num_toe.clear()
            self.clients.clear()                        # avoid dual-definition

            pl = get_local_portlist()

            if self.OptModeFlag == 0:
                self.zb_num = len(pl)

                self.num_sum.append(self.zb_num)
                self.num_head.append(0)
                self.num_toe.append(self.zb_num)

                self.set_zb_table_format()
                self.set_table_number(self.zb_num)

                self.sb.showMessage(str(self.zb_num) + ' port(s) found in PC.')
                if self.zb_num > 0:
                    for n in range(self.zb_num):
                        com_name = 'p' + str(n)
                        globals()[com_name] = SerialPort(pl[n])
                        self.zb_selist.append([n, 0])
                    self.show_portname(self.zb_num, pl, 0, str(get_local_ip()))
                    # self.btnGenSelect.setEnabled(True)
                    self.set_mode_btn_state(self.OptModeFlag, True)
                else:
                    # self.btnGenSelect.setEnabled(False)
                    self.set_mode_btn_state(self.OptModeFlag, False)
                    self.msg = QMessageBox.information(self, 'Error',
                                                       'No serial port(s) found, please plug port(s) and retry.')

            elif self.OptModeFlag == 1:
                self.blm_num = len(pl)

                self.num_sum.append(self.blm_num)
                self.num_head.append(0)
                self.num_toe.append(self.blm_num)

                self.set_blm_table_format()
                self.set_table_number(self.blm_num)

                self.sb.showMessage(str(self.blm_num) + ' port(s) found in PC.')
                if self.blm_num > 0:
                    for n in range(self.blm_num):
                        com_name = 'p' + str(n)
                        globals()[com_name] = SerialPort(pl[n])
                        self.blm_selist.append([n, 0])
                    self.show_portname(self.blm_num, pl, 0, 'local')
                    # self.btnGenSelect.setEnabled(True)
                    self.set_mode_btn_state(self.OptModeFlag, True)
                else:
                    self.btnGenSelect.setEnabled(False)
                    # self.set_mode_btn_state(self.OptModeFlag, False)
                    self.msg = QMessageBox.information(self, 'Error',
                                                       'No serial port(s) found, please plug port(s) and retry.')
            else:
                pass

    def gen_software(self):
        self.sw = Software()
        self.sw.show()

    def gen_version(self):
        self.ver = Version()
        self.ver.show()

    def show_portname(self, num, lst, clt_id, clt_ip):
        for i in range(num):
            self.set_data_cb(i, i, clt_id, clt_ip)
            self.set_data_com(i, lst[i])
        self.tblLayout.addWidget(self.table)

    def show_remote_portname(self, num, no, lst, clt_id):
        self.set_data_cb(num, no, clt_id, str(self.clients_info[clt_id-1][1]))
        self.set_data_com(num, lst[no])
        self.tblLayout.addWidget(self.table)

    def set_data_cb(self, index, indx, clt_id, clt_ip):
        self.cb_demo = QCheckBox()
        self.cb_demo.setText(str(indx+1))
        c = QHBoxLayout()
        c.setAlignment(Qt.AlignCenter)
        c.addWidget(self.cb_demo)
        self.cw = QWidget()
        self.cw.setLayout(c)
        self.table.setCellWidget(index, 0, self.cw)
        self.ip_demo = QTableWidgetItem(str(clt_ip))
        self.ip_demo.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 2, self.ip_demo)
        self.table_data_lines.append([index, self.cb_demo, indx, clt_id, clt_ip])

    def set_data_com(self, index, com):
        self.com_demo = QTableWidgetItem(str(com))
        self.com_demo.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(index, 1, self.com_demo)

    def set_opt_rsp(self, index, rsp, state):
        self.rsp_demo = QTableWidgetItem(str(rsp))
        if state:
            self.rsp_demo.setForeground(QBrush(QColor(255, 0, 0)))          # red
        else:
            self.rsp_demo.setForeground(QBrush(QColor(0, 170, 0)))          # green
        self.rsp_demo.setTextAlignment(Qt.AlignCenter)

        if self.OptModeFlag == 0:
            self.table.setItem(index, 8, self.rsp_demo)
        elif self.OptModeFlag == 1:
            self.table.setItem(index, 7, self.rsp_demo)
        else:
            pass

    # used for context menu
    def single_send(self, index, cmd):
        try:
            if not globals()['p' + str(index)].state():
                self.msg = QMessageBox.information(self, 'Error', 'port is not open.')
            else:
                if index <= self.blm_num or index <= self.zb_num:
                    format_cmd = cmd + '\r\n'
                    get_info = globals()['p' + str(index)].sendcmd(str(format_cmd))
                    self.tbOutText.appendPlainText(str(globals()['p' + str(index)].portname) + ' : ' + str(get_info))
                    self.tbCLLog.append('send: ' + str(cmd) + ' to port # ' + str(index))
                else:
                    self.tbCLLog.append('only support local port.')
        except Exception as e:
            self.tbCLLog.append('single_send: ' + repr(e))

    # used for flash program
    def set_data_processbar(self, index, value):
        self.pb_demo = QProgressBar()
        self.pb_demo.setValue(value)
        if self.OptModeFlag == 0:
            self.table.setItem(index, 9, self.pb_demo)
        elif self.OptModeFlag == 1:
            self.table.setItem(index, 8, self.pb_demo)
        else:
            pass

    def event_zbRunScpt(self):
        scpt = QFileDialog.getOpenFileName(self, 'Select Script', '', 'Python Files(*.py)')
        pass

    def event_zbLdCfg(self):
        self.msg = QMessageBox.information(self, 'Notice', 'Unimplemented function.')

    def event_zbSvCfg(self):
        self.msg = QMessageBox.information(self, 'Notice', 'Unimplemented function.')

    def event_zbProgram(self):
        self.pd = ProgramDlg()
        self.pd.exec_()

    def local_print(self, i, rsps):
        try:
            self.tbOutText.appendPlainText(str(i+1)+' '+str(globals()['p' + str(i)].portname))
            self.tbOutText.appendPlainText(''.join(rsps))
            # self.pbGen.setValue(i+1)
            self.tbCLLog.append(str(self.charcmd) + ' : thread for #' + str(i+1) + ' port is in process...')
        except Exception as e:
            self.tbOutText.appendPlainText('local_print: ' + str(e))

    def event_GenSend(self):            # local
        self.charcmd = self.lineGenCmd.text()
        if self.OptModeFlag == 0:
            if self.charcmd.isalpha() or self.charcmd.isdigit():
                for zs in self.zb_selist:
                    self.wkr3 = ZbWorker(zs[0], self.charcmd)
                    self.thd3 = QThread()
                    self.threads.append((self.thd3, self.wkr3))
                    self.wkr3.sig_zb.connect(self.local_print)
                    self.wkr3.moveToThread(self.thd3)
                    self.thd3.started.connect(self.wkr3.work_zb_getrsp)
                    self.thd3.start()
            else:
                self.msg = QMessageBox().information(self, 'Error', 'Invalid command type.')
        elif self.OptModeFlag == 1:
            format_cmd = self.charcmd + '\r\n'
            for bs in self.blm_selist:
                self.wkr3 = BlmWorker(bs[0], str(format_cmd))
                self.thd3 = QThread()
                self.threads.append((self.thd3, self.wkr3))
                self.wkr3.sig_zb.connect(self.local_print)
                self.wkr3.moveToThread(self.thd3)
                self.thd3.started.connect(self.wkr3.work_blm_getrsp)
                self.thd3.start()
        else:
            pass

    def event_GenSelect(self):
        try:
            if self.zbToggle.isChecked() or self.blmToggle.isChecked():
                self.msg = QMessageBox.information(self, 'Error', 'Please close all port(s) first and select.')
            else:
                if self.OptModeFlag == 0:
                    for line in self.table_data_lines:
                        if line[1].isChecked():
                            if [line[2], line[3]] not in self.zb_selist:
                                self.zb_selist.append([line[2], line[3]])
                            self.set_opt_rsp(line[0], 'selected', 0)
                        else:
                            if [line[2], line[3]] in self.zb_selist:
                                self.zb_selist.remove([line[2], line[3]])
                            self.set_opt_rsp(line[0], '-', 0)
                    self.tbCLLog.append('Selected zb port(s) = ' + str([zs[0]+1 for zs in self.zb_selist]))

                elif self.OptModeFlag == 1:
                    for line in self.table_data_lines:
                        if line[1].isChecked():
                            if [line[2], line[3]] not in self.blm_selist:       # [port_id, client_id]
                                self.blm_selist.append([line[2], line[3]])
                            self.set_opt_rsp(line[0], 'selected', 0)
                        else:
                            if [line[2], line[3]] in self.blm_selist:
                                self.blm_selist.remove([line[2], line[3]])
                            self.set_opt_rsp(line[0], '-', 0)
                    self.tbCLLog.append('Selected blm port(s) = ' + str([bs[0]+1 for bs in self.blm_selist]))
                else:
                    pass
        except Exception as e:
            self.tbCLLog.append('event_GenSelect: ' + repr(e))

    def event_GenLog(self):
        logflow = self.tbOutText.toPlainText()
        if logflow:
            text_name = datetime.datetime.now().strftime('log%Y-%m-%d-%H-%M-%S.txt')
            self.Log = open(str(text_name), 'w+')
            self.Log.write(str(logflow))
            self.Log.close()
            self.tbCLLog.append('generate log.txt in current working dir.')
        else:
            self.tbCLLog.append('no log needs to save.')

    def event_GenCln(self):
        self.tbOutText.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = ezLNTDemo()
    lw = LogWindow()
    lw.show()
    sys.exit(app.exec_())
