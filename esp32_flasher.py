#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ESP32 firmware updater with a borderless, rounded eight-language UI."""
import ctypes
import json
import os
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

import esptool
import serial.tools.list_ports

LANGUAGES = {"en": "English", "zh": "简体中文", "ja": "日本語", "ko": "한국어", "ru": "Русский", "de": "Deutsch", "fr": "Français", "es": "Español"}
LANGUAGE_LABELS = {"en": "Language:", "zh": "语言：", "ja": "言語：", "ko": "언어:", "ru": "Язык:", "de": "Sprache:", "fr": "Langue :", "es": "Idioma:"}
FONT_FAMILY = "SimHei"


def enable_dpi_awareness():
    """Enable crisp font rendering before Tk creates the native window."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()


T = {
"en": ["Firmware Updater","Serial Port Settings","Select port:","Refresh","Baud rate:","Update Notes","Firmware version to install: {version}","No update notes available.","● System ready","● Serial-port list refreshed","● No serial devices found","Start Update","Updating…","Updating firmware, please wait…","Update Complete","The firmware update is complete.","Update Failed","An error occurred during the update:\n\n{error}","Warning","An update is already in progress. Please wait.","Error","Please select a serial port first.","These firmware files are missing:\n{files}","Confirm Update","Firmware version: {version}\nSerial port: {port}\n\nContinue?","Confirm Exit","Close the firmware updater?","The firmware is being updated and cannot be closed. Please wait until it finishes.","© SkyLensman · All rights reserved","Copyright Notice","Copyright © SkyLensman / 摄天科技（哈尔滨）有限公司.\n\nAll rights reserved. Unauthorized modification, copying, distribution, forwarding, or commercial use of this software and its contents is prohibited."],
"zh": ["固件升级程序","串口设置","选择串口：","刷新","波特率：","更新日志","将要升级的固件版本：{version}","暂无更新日志。","● 系统就绪","● 串口列表已刷新","● 未检测到串口设备","开始升级","升级中…","正在升级固件，请稍候…","升级完成","固件升级已完成。","升级失败","升级过程中发生错误：\n\n{error}","警告","正在升级中，请稍候。","错误","请先选择串口。","以下固件文件不存在：\n{files}","确认升级","固件版本：{version}\n串口：{port}\n\n确定继续吗？","确认退出","确定要关闭固件升级程序吗？","固件正在升级，无法关闭程序。请等待升级完成。","© SkyLensman · 版权所有","版权声明","版权所有 © SkyLensman / 摄天科技（哈尔滨）有限公司。\n\n保留所有权利。未经授权，严禁修改、复制、传播、转发或将本软件及其内容用于商业用途。"],
"ja": ["ファームウェア更新","シリアルポート設定","ポートを選択：","更新","ボーレート：","更新内容","インストールするファームウェア：{version}","更新内容はありません。","● 準備完了","● ポート一覧を更新しました","● シリアルデバイスが見つかりません","更新を開始","更新中…","ファームウェアを更新しています。お待ちください…","更新完了","ファームウェアの更新が完了しました。","更新失敗","更新中にエラーが発生しました：\n\n{error}","警告","更新処理中です。お待ちください。","エラー","最初にシリアルポートを選択してください。","次のファームウェアファイルが見つかりません：\n{files}","更新の確認","ファームウェア：{version}\nポート：{port}\n\n続行しますか？","終了の確認","ファームウェア更新を終了しますか？","更新中はアプリケーションを閉じられません。完了するまでお待ちください。","© SkyLensman · 無断転載禁止","著作権表示","著作権 © SkyLensman / 摄天科技（哈尔滨）有限公司。\n\n無断での改変、複製、配布、転送、または商用利用を禁じます。"],
"ko": ["펌웨어 업데이트","직렬 포트 설정","포트 선택:","새로 고침","전송 속도:","업데이트 정보","설치할 펌웨어 버전: {version}","업데이트 정보가 없습니다.","● 시스템 준비 완료","● 포트 목록을 새로 고쳤습니다","● 직렬 장치를 찾을 수 없습니다","업데이트 시작","업데이트 중…","펌웨어를 업데이트하고 있습니다. 잠시 기다려 주세요…","업데이트 완료","펌웨어 업데이트가 완료되었습니다.","업데이트 실패","업데이트 중 오류가 발생했습니다:\n\n{error}","경고","업데이트가 진행 중입니다. 잠시 기다려 주세요.","오류","먼저 직렬 포트를 선택하세요.","다음 펌웨어 파일이 없습니다:\n{files}","업데이트 확인","펌웨어 버전: {version}\n포트: {port}\n\n계속하시겠습니까?","종료 확인","펌웨어 업데이트를 종료하시겠습니까?","업데이트 중에는 응용 프로그램을 닫을 수 없습니다. 완료될 때까지 기다려 주세요.","© SkyLensman · 판권 소유","저작권 고지","저작권 © SkyLensman / 摄天科技（哈尔滨）有限公司.\n\n무단 수정, 복제, 배포, 전달 또는 상업적 이용을 금지합니다."],
"ru": ["Обновление прошивки","Настройки последовательного порта","Выберите порт:","Обновить","Скорость:","Сведения об обновлении","Версия прошивки для установки: {version}","Нет сведений об обновлении.","● Система готова","● Список портов обновлён","● Последовательные устройства не найдены","Начать обновление","Обновление…","Выполняется обновление прошивки, подождите…","Обновление завершено","Обновление прошивки завершено.","Ошибка обновления","Во время обновления произошла ошибка:\n\n{error}","Предупреждение","Обновление уже выполняется. Подождите.","Ошибка","Сначала выберите последовательный порт.","Следующие файлы прошивки отсутствуют:\n{files}","Подтвердите обновление","Версия прошивки: {version}\nПорт: {port}\n\nПродолжить?","Подтвердите выход","Закрыть программу обновления?","Во время обновления приложение нельзя закрыть. Дождитесь завершения.","© SkyLensman · Все права защищены","Уведомление об авторских правах","Авторские права © SkyLensman / 摄天科技（哈尔滨）有限公司.\n\nВсе права защищены. Несанкционированные изменение, копирование, распространение, пересылка или коммерческое использование запрещены."],
"de": ["Firmware-Aktualisierung","Serielle Schnittstelle","Port auswählen:","Aktualisieren","Baudrate:","Versionshinweise","Zu installierende Firmware-Version: {version}","Keine Versionshinweise verfügbar.","● System bereit","● Portliste aktualisiert","● Keine seriellen Geräte gefunden","Update starten","Aktualisierung…","Firmware wird aktualisiert, bitte warten…","Update abgeschlossen","Die Firmware wurde aktualisiert.","Aktualisierung fehlgeschlagen","Während der Aktualisierung ist ein Fehler aufgetreten:\n\n{error}","Warnung","Eine Aktualisierung läuft bereits. Bitte warten.","Fehler","Bitte wählen Sie zuerst einen seriellen Port.","Folgende Firmware-Dateien fehlen:\n{files}","Update bestätigen","Firmware-Version: {version}\nPort: {port}\n\nFortfahren?","Beenden bestätigen","Firmware-Updater schließen?","Während der Aktualisierung kann die Anwendung nicht geschlossen werden. Bitte warten Sie bis zum Abschluss.","© SkyLensman · Alle Rechte vorbehalten","Urheberrechtshinweis","Urheberrecht © SkyLensman / 摄天科技（哈尔滨）有限公司.\n\nAlle Rechte vorbehalten. Unbefugtes Ändern, Kopieren, Verbreiten, Weiterleiten oder kommerzielles Nutzen ist untersagt."],
"fr": ["Mise à jour du micrologiciel","Paramètres du port série","Sélectionner le port :","Actualiser","Débit :","Notes de mise à jour","Version du micrologiciel à installer : {version}","Aucune note de mise à jour.","● Système prêt","● Liste des ports actualisée","● Aucun périphérique série détecté","Démarrer la mise à jour","Mise à jour…","Mise à jour du micrologiciel, veuillez patienter…","Mise à jour terminée","La mise à jour du micrologiciel est terminée.","Échec de la mise à jour","Une erreur est survenue durant la mise à jour :\n\n{error}","Avertissement","Une mise à jour est déjà en cours. Veuillez patienter.","Erreur","Sélectionnez d’abord un port série.","Les fichiers de micrologiciel suivants sont introuvables :\n{files}","Confirmer la mise à jour","Version : {version}\nPort : {port}\n\nContinuer ?","Confirmer la fermeture","Fermer l’outil de mise à jour ?","L’application ne peut pas être fermée pendant la mise à jour. Veuillez attendre la fin.","© SkyLensman · Tous droits réservés","Avis de droit d’auteur","Droits d’auteur © SkyLensman / 摄天科技（哈尔滨）有限公司.\n\nTous droits réservés. Toute modification, copie, diffusion, retransmission ou utilisation commerciale non autorisée est interdite."],
"es": ["Actualización de firmware","Configuración del puerto serie","Seleccionar puerto:","Actualizar","Velocidad:","Notas de actualización","Versión de firmware que se instalará: {version}","No hay notas de actualización.","● Sistema listo","● Lista de puertos actualizada","● No se encontraron dispositivos serie","Iniciar actualización","Actualizando…","Actualizando el firmware, espere…","Actualización completada","La actualización de firmware ha terminado.","Error de actualización","Se produjo un error durante la actualización:\n\n{error}","Advertencia","Ya hay una actualización en curso. Espere.","Error","Seleccione primero un puerto serie.","Faltan estos archivos de firmware:\n{files}","Confirmar actualización","Versión de firmware: {version}\nPuerto: {port}\n\n¿Continuar?","Confirmar salida","¿Cerrar el actualizador de firmware?","La aplicación no se puede cerrar durante la actualización. Espere hasta que termine.","© SkyLensman · Todos los derechos reservados","Aviso de copyright","Copyright © SkyLensman / 摄天科技（哈尔滨）有限公司.\n\nTodos los derechos reservados. Se prohíben la modificación, copia, distribución, reenvío o uso comercial no autorizados."],
}
KEYS = "title port_settings select_port refresh baud notes version no_notes ready refreshed no_ports start updating working success success_message failed failed_message warning already error select_first missing confirm confirm_message exit exit_message cannot_close copyright copyright_title copyright_message".split()

class RoundedButton(tk.Canvas):
    """Canvas button with rounded corners and a Button-compatible config API."""
    def __init__(self, parent, command, normal_bg, hover_bg, disabled_bg,
                 width=172, height=46, radius=12):
        super().__init__(parent, width=width, height=height, bd=0,
                         highlightthickness=0, bg=parent.cget("bg"), cursor="hand2")
        self.command = command
        self.normal_bg = normal_bg
        self.hover_bg = hover_bg
        self.disabled_bg = disabled_bg
        self.button_text = ""
        self.button_state = "normal"
        self.hovered = False
        self.radius = radius
        self.button_width = width
        self.button_height = height
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonRelease-1>", self._release)
        self._draw()

    def _draw(self):
        self.delete("all")
        if self.button_state == "disabled":
            color = self.disabled_bg
        else:
            color = self.hover_bg if self.hovered else self.normal_bg
        width, height, radius = self.button_width, self.button_height, self.radius
        self.create_rectangle(radius, 0, width - radius, height, fill=color, outline=color)
        self.create_rectangle(0, radius, width, height - radius, fill=color, outline=color)
        self.create_oval(0, 0, radius * 2, radius * 2, fill=color, outline=color)
        self.create_oval(width - radius * 2, 0, width, radius * 2, fill=color, outline=color)
        self.create_oval(0, height - radius * 2, radius * 2, height, fill=color, outline=color)
        self.create_oval(width - radius * 2, height - radius * 2, width, height, fill=color, outline=color)
        self.create_text(width / 2, height / 2, text=self.button_text, fill="white",
                         font=(FONT_FAMILY, 12, "bold"))

    def _enter(self, event=None):
        if self.button_state != "disabled":
            self.hovered = True
            self._draw()

    def _leave(self, event=None):
        self.hovered = False
        self._draw()

    def _release(self, event=None):
        if self.button_state != "disabled" and self.command:
            self.command()

    def configure(self, cnf=None, **kwargs):
        if isinstance(cnf, dict):
            kwargs.update(cnf)
        if "text" in kwargs:
            self.button_text = kwargs.pop("text")
        if "state" in kwargs:
            self.button_state = kwargs.pop("state")
        if "bg" in kwargs:
            color = kwargs.pop("bg")
            self.normal_bg = color
            if self.button_state == "disabled":
                self.disabled_bg = color
        if kwargs:
            super().configure(**kwargs)
        super().configure(cursor="arrow" if self.button_state == "disabled" else "hand2")
        self._draw()

    config = configure

class ESP32Flasher:
    def __init__(self, root):
        self.root, self.language, self.is_flashing = root, "en", False
        self.title_click_times = []
        self.hwnd = None
        self.base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        self.colors = {"dark":"#1e1e1e", "medium":"#2d2d30", "light":"#3e3e42", "accent":"#007acc", "hover":"#1c97ea", "text":"#e0e0e0", "dim":"#a8a8a8", "warning":"#ce9178", "success":"#4ec9b0", "error":"#f48771"}
        root.overrideredirect(True); root.geometry("700x690"); root.resizable(False, False); root.configure(bg=self.colors["dark"])
        self.configure_fonts(); self.configure_native_window(); self.load_config(); self.create_widgets(); self.refresh_ports()
        self.root.bind("<Map>", self.on_window_map, add="+")

    def s(self, key, **kwargs): return dict(zip(KEYS, T[self.language]))[key].format(**kwargs)
    def path(self, name): return name if os.path.isabs(name) else os.path.join(self.base_dir, name)
    def configure_fonts(self):
        """Use SimHei throughout and match Tk point scaling to the active DPI."""
        try:
            self.root.tk.call("tk", "scaling", self.root.winfo_fpixels("1i") / 72.0)
        except tk.TclError:
            pass
        for font_name, size in (("TkDefaultFont", 10), ("TkTextFont", 10),
                                ("TkMenuFont", 10), ("TkHeadingFont", 11),
                                ("TkCaptionFont", 10), ("TkSmallCaptionFont", 9)):
            try:
                tkfont.nametofont(font_name).configure(family=FONT_FAMILY, size=size)
            except tk.TclError:
                pass
    def configure_native_window(self):
        """Use DWM anti-aliased corners and keep the borderless window on the taskbar."""
        if sys.platform != "win32":
            return
        self.root.update_idletasks()
        user32 = ctypes.windll.user32
        child_hwnd = self.root.winfo_id()
        self.hwnd = user32.GetParent(child_hwnd) or child_hwnd

        # An overrideredirect window normally behaves like a tool window. Switching
        # it to APPWINDOW gives it a stable taskbar button while retaining our UI.
        gwl_exstyle = -20
        ws_ex_toolwindow = 0x00000080
        ws_ex_appwindow = 0x00040000
        exstyle = user32.GetWindowLongW(self.hwnd, gwl_exstyle)
        exstyle = (exstyle & ~ws_ex_toolwindow) | ws_ex_appwindow
        user32.SetWindowLongW(self.hwnd, gwl_exstyle, exstyle)

        # Remove the old hard-clipped region, then ask Windows 11 DWM to draw
        # smooth, anti-aliased corners. Retain a region fallback for older Windows.
        user32.SetWindowRgn(self.hwnd, 0, True)
        preference = ctypes.c_int(2)  # DWMWCP_ROUND
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            self.hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
        if result != 0:
            region = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, 701, 691, 24, 24)
            user32.SetWindowRgn(self.hwnd, region, True)

        swp_flags = 0x0001 | 0x0002 | 0x0004 | 0x0020
        user32.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0, swp_flags)

    def on_window_map(self, event=None):
        self.root.after_idle(self.configure_native_window)
    def load_config(self):
        try:
            with open(self.path("config.json"), encoding="utf-8") as f: self.config = json.load(f)
        except Exception: self.config = {"firmware_version":"v1.0.0", "baud_rate":921600, "chip":"esp32", "update_log":[], "firmware_files":[]}
    def label(self, parent, size=10, bold=False): return tk.Label(parent, bg=self.colors["medium"], fg=self.colors["text"], font=(FONT_FAMILY, size, "bold" if bold else "normal"))
    def button(self, parent, command, small=False):
        base, hover = (self.colors["light"], "#454545") if small else (self.colors["accent"], self.colors["hover"])
        if not small:
            return RoundedButton(parent, command, base, hover, self.colors["light"])
        b = tk.Button(parent, command=command, bg=base, fg=self.colors["text"] if small else "white", bd=0, padx=15 if small else 30, pady=5 if small else 12, cursor="hand2", font=(FONT_FAMILY,10) if small else (FONT_FAMILY,12,"bold"))
        b.bind("<Enter>", lambda e: b.config(bg=hover)); b.bind("<Leave>", lambda e: b.config(bg=base)); return b
    def card(self, parent, height=None):
        f=tk.Frame(parent,bg=self.colors["medium"],height=height); i=tk.Frame(f,bg=self.colors["medium"]); i.pack(fill="x",padx=15,pady=15); return f,i
    def create_widgets(self):
        st=ttk.Style(); st.theme_use("clam"); st.configure("TCombobox",fieldbackground=self.colors["light"],background=self.colors["light"],foreground=self.colors["text"],arrowcolor=self.colors["text"],font=(FONT_FAMILY,10)); st.configure("TProgressbar",background=self.colors["accent"],troughcolor=self.colors["medium"])
        st.configure("Language.TCombobox", fieldbackground="#f2f2f2", background="#f2f2f2",
                     foreground="#000000", arrowcolor="#000000", font=(FONT_FAMILY,10))
        st.map("Language.TCombobox",
               fieldbackground=[("readonly", "#f2f2f2")],
               foreground=[("readonly", "#000000")],
               selectbackground=[("readonly", "#f2f2f2")],
               selectforeground=[("readonly", "#000000")])
        self.root.option_add("*TCombobox*Listbox.background",self.colors["light"]); self.root.option_add("*TCombobox*Listbox.foreground",self.colors["text"])
        bar=tk.Frame(self.root,bg=self.colors["medium"],height=38); bar.pack(fill="x"); bar.pack_propagate(False)
        self.top_title=tk.Label(bar,bg=self.colors["medium"],fg=self.colors["text"],font=(FONT_FAMILY,10,"bold"),cursor="hand2"); self.top_title.pack(side="left",padx=16)
        close=tk.Button(bar,text="×",command=self.close_window,bg=self.colors["medium"],fg=self.colors["text"],bd=0,width=3,font=("Segoe UI",13),cursor="hand2"); close.pack(side="right",fill="y"); close.bind("<Enter>",lambda e:close.config(bg="#e81123")); close.bind("<Leave>",lambda e:close.config(bg=self.colors["medium"]))
        mini=tk.Button(bar,text="−",command=self.minimize,bg=self.colors["medium"],fg=self.colors["text"],bd=0,width=3,font=("Segoe UI Symbol",12),cursor="hand2"); mini.pack(side="right",fill="y")
        self.close_button, self.minimize_button = close, mini
        for window_button in (self.close_button, self.minimize_button):
            window_button.config(width=4, bd=0, relief="flat", highlightthickness=0,
                                 padx=0, pady=0, font=("Segoe UI Symbol", 13),
                                 activeforeground="white")
        self.minimize_button.config(font=("Segoe UI Symbol", 12))
        self.minimize_button.config(activebackground=self.colors["light"])
        self.minimize_button.bind("<Enter>", lambda e: self.minimize_button.config(bg=self.colors["light"]))
        self.minimize_button.bind("<Leave>", lambda e: self.minimize_button.config(bg=self.colors["medium"]))
        self.close_button.config(activebackground="#e81123")

        # Copyright remains hidden from the interface; the top-left application
        # title is the discreet entry point for the three-click notice.
        self.lang=ttk.Combobox(bar,width=12,state="readonly",style="Language.TCombobox",font=(FONT_FAMILY,10),values=list(LANGUAGES.values()))
        self.lang.set(LANGUAGES[self.language]); self.lang.pack(side="right",padx=(5,8),pady=6)
        self.lang.bind("<<ComboboxSelected>>",self.change_language)
        self.lang_label=tk.Label(bar,bg=self.colors["medium"],fg=self.colors["text"],font=(FONT_FAMILY,10))
        self.lang_label.pack(side="right",padx=(8,0))
        bar.bind("<Button-1>",self.drag_start); bar.bind("<B1-Motion>",self.drag)
        self.top_title.bind("<Button-1>",self.title_pressed); self.top_title.bind("<B1-Motion>",self.drag)
        header=tk.Frame(self.root,bg=self.colors["medium"],height=76); header.pack(fill="x"); header.pack_propagate(False); self.heading=tk.Label(header,bg=self.colors["medium"],fg=self.colors["accent"],font=(FONT_FAMILY,20,"bold")); self.heading.pack(pady=(13,15))
        main=tk.Frame(self.root,bg=self.colors["dark"]); main.pack(fill="both",expand=True,padx=20,pady=(18,17))
        f,i=self.card(main); f.pack(fill="x",pady=(0,15)); self.port_section=self.label(i,11,True); self.port_section.grid(row=0,column=0,columnspan=3,sticky="w",pady=(0,10)); self.port_l=self.label(i); self.port_l.grid(row=1,column=0,sticky="w",pady=5)
        self.port_combo=ttk.Combobox(i,width=36,state="readonly",font=(FONT_FAMILY,10)); self.port_combo.grid(row=1,column=1,padx=10,pady=5); self.refresh_b=self.button(i,self.refresh_ports,True); self.refresh_b.grid(row=1,column=2,padx=5,pady=5)
        self.baud_l=self.label(i); self.baud_l.grid(row=2,column=0,sticky="w",pady=5); self.baud=ttk.Combobox(i,width=36,state="readonly",font=(FONT_FAMILY,10),values=["115200","460800","921600","1500000"]); self.baud.set(str(self.config.get("baud_rate",921600))); self.baud.grid(row=2,column=1,padx=10,pady=5)
        f,i=self.card(main,200); f.pack(fill="x",pady=(0,15)); f.pack_propagate(False); self.notes_l=self.label(i,11,True); self.notes_l.pack(anchor="w",pady=(0,10)); self.log=tk.Text(i,height=6,width=70,bg=self.colors["light"],fg=self.colors["text"],bd=0,padx=15,pady=12,font=(FONT_FAMILY,10),state="disabled",wrap="word"); self.log.pack()
        self.progress=ttk.Progressbar(main,mode="indeterminate",length=660); self.progress.pack(pady=(5,10)); self.status=tk.Label(main,bg=self.colors["dark"],fg=self.colors["accent"],font=(FONT_FAMILY,10)); self.status.pack(pady=(0,15)); self.flash=self.button(main,self.start_flash); self.flash.pack(pady=(7,0))
        self.render()
    def render(self):
        self.root.title(self.s("title")); self.top_title.config(text=self.s("title")); self.lang_label.config(text=LANGUAGE_LABELS[self.language]); self.heading.config(text=self.s("title")); self.port_section.config(text=self.s("port_settings")); self.port_l.config(text=self.s("select_port")); self.refresh_b.config(text=self.s("refresh")); self.baud_l.config(text=self.s("baud")); self.notes_l.config(text=self.s("notes")); self.flash.config(text=self.s("updating") if self.is_flashing else self.s("start")); self.update_log(); self.set_status(self.s("ready"))
    def change_language(self,event=None): self.language=next(k for k,v in LANGUAGES.items() if v==self.lang.get()); self.render(); self.refresh_ports()
    def update_log(self):
        lines=[self.s("version",version=self.config.get("firmware_version","v1.0.0")),"─"*60]+(self.config.get("update_log") or [self.s("no_notes")]); self.log.config(state="normal"); self.log.delete("1.0",tk.END); self.log.insert("1.0","\n".join(lines)); self.log.config(state="disabled")
    def set_status(self,text,color=None): self.status.config(text=text,fg=color or self.colors["accent"])
    def refresh_ports(self):
        ports=[f"{p.device} - {p.description}" for p in serial.tools.list_ports.comports()]; self.port_combo["values"]=ports
        if ports: self.port_combo.current(0); self.set_status(self.s("refreshed"))
        else: self.set_status(self.s("no_ports"),self.colors["warning"])
    def start_flash(self):
        if self.is_flashing: return messagebox.showwarning(self.s("warning"),self.s("already"))
        if not self.port_combo.get(): return messagebox.showerror(self.s("error"),self.s("select_first"))
        missing=[x["file"] for x in self.config.get("firmware_files",[]) if not os.path.exists(self.path(x["file"]))]
        if missing: return messagebox.showerror(self.s("error"),self.s("missing",files="\n".join(missing)))
        port=self.port_combo.get().split(" - ")[0]; version=self.config.get("firmware_version","v1.0.0")
        if not messagebox.askyesno(self.s("confirm"),self.s("confirm_message",version=version,port=port)): return
        self.is_flashing=True; self.flash.config(state="disabled",text=self.s("updating"),bg=self.colors["light"]); self.progress.start(); self.set_status(self.s("working"),self.colors["warning"]); threading.Thread(target=self.flash_firmware,args=(port,),daemon=True).start()
    def flash_firmware(self,port):
        try:
            args=["--chip",self.config.get("chip","esp32"),"--port",port,"--baud",self.baud.get(),"write_flash"]
            for fw in self.config.get("firmware_files",[]): args += [fw["address"],self.path(fw["file"])]
            old=sys.argv
            try: sys.argv=["esptool.py"]+args; esptool.main(); self.root.after(0,self.flash_success)
            except SystemExit as e: self.root.after(0,self.flash_success if e.code==0 else self.flash_error,*(() if e.code==0 else (f"Exit code: {e.code}",)))
            finally: sys.argv=old
        except Exception as e: self.root.after(0,self.flash_error,str(e))
    def flash_success(self): self.progress.stop(); self.is_flashing=False; self.flash.config(state="normal",text=self.s("start"),bg=self.colors["accent"]); self.set_status("✓ "+self.s("success"),self.colors["success"]); messagebox.showinfo(self.s("success"),self.s("success_message"))
    def flash_error(self,error): self.progress.stop(); self.is_flashing=False; self.flash.config(state="normal",text=self.s("start"),bg=self.colors["accent"]); self.set_status("✕ "+self.s("failed"),self.colors["error"]); messagebox.showerror(self.s("failed"),self.s("failed_message",error=error))
    def title_clicked(self, event=None):
        now = time.monotonic()
        self.title_click_times = [stamp for stamp in self.title_click_times if now - stamp <= 2.0]
        self.title_click_times.append(now)
        if len(self.title_click_times) >= 3:
            self.title_click_times.clear()
            self.show_copyright()

    def title_pressed(self, event):
        self.drag_start(event)
        self.title_clicked(event)

    def show_copyright(self,event=None): messagebox.showinfo(self.s("copyright_title"),self.s("copyright_message"))
    def drag_start(self,event): self.dx,self.dy=event.x,event.y
    def drag(self,event): self.root.geometry(f"+{self.root.winfo_x()+event.x-self.dx}+{self.root.winfo_y()+event.y-self.dy}")
    def minimize(self):
        if sys.platform == "win32":
            self.configure_native_window()
            ctypes.windll.user32.ShowWindow(self.hwnd, 6)  # SW_MINIMIZE: remains on taskbar
        else:
            self.root.iconify()
    def close_window(self):
        if self.is_flashing: return messagebox.showwarning(self.s("warning"),self.s("cannot_close"))
        if messagebox.askyesno(self.s("exit"),self.s("exit_message")): self.root.destroy()

if __name__ == "__main__":
    enable_dpi_awareness()
    root=tk.Tk(); ESP32Flasher(root); root.mainloop()
