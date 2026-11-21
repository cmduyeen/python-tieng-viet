"""Unit & integration tests cho vpy."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from vpy import cli, error_translator, transpiler


class TestVPy(unittest.TestCase):
    def _run_cli(self, args: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_huongdan_and_version(self) -> None:
        code, out, _ = self._run_cli(["huongdan"])
        self.assertEqual(code, 0)
        self.assertIn("vpy chay", out)

        code_v, out_v, _ = self._run_cli(["--version"])
        self.assertEqual(code_v, 0)
        self.assertIn("0.1.0", out_v)

    def test_transpiler_preserves_strings_and_comments(self) -> None:
        vpy_src = (
            '# Day la comment co chu neu va ham\n'
            'ham tong(a, b):\n'
            '    neu a > 0 va Dung:\n'
            '        trave a + b\n'
            '    nguoclai:\n'
            '        trave 0\n'
            'in("neu khong dung trong chuoi", tong(2, 3))\n'
        )
        py_src = transpiler.transpile_vpy_to_py(vpy_src)
        self.assertIn("def tong", py_src)
        self.assertIn("if a > 0 and True:", py_src)
        self.assertIn("return a + b", py_src)
        self.assertIn("else:", py_src)
        self.assertIn('print("neu khong dung trong chuoi"', py_src)
        self.assertIn("# Day la comment co chu neu va ham", py_src)

    def test_run_vpy_and_dich(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            orig = os.getcwd()
            os.chdir(tmp)
            try:
                vpy_file = Path(tmp) / "bai1.vpy"
                vpy_file.write_text(
                    'voi i trong dayso(3):\n'
                    '    in("So:", i)\n',
                    encoding="utf-8",
                )
                code, out, _ = self._run_cli(["chay", "bai1.vpy"])
                self.assertEqual(code, 0)
                self.assertIn("So: 0", out)
                self.assertIn("So: 2", out)

                code_d, _, _ = self._run_cli(["dich", "bai1.vpy"])
                self.assertEqual(code_d, 0)
                self.assertTrue((Path(tmp) / "bai1.py").exists())
            finally:
                os.chdir(orig)

    def test_error_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            orig = os.getcwd()
            os.chdir(tmp)
            try:
                bad_file = Path(tmp) / "loi.py"
                bad_file.write_text("print(bien_chua_tao)\n", encoding="utf-8")
                code, out, err = self._run_cli(["chay", "loi.py"])
                self.assertNotEqual(code, 0)
                self.assertIn("Chua khai bao ten 'bien_chua_tao'", err)
                self.assertIn("dong 1", err)
            finally:
                os.chdir(orig)

    def test_user_line_extraction_and_token_error(self) -> None:
        tb = (
            'Traceback (most recent call last):\n'
            '  File "C:\\Temp\\vpy_ide_abc.py", line 2, in <module>\n'
            '  File "C:\\Python312\\Lib\\encodings\\cp1258.py", line 19, in encode\n'
            'UnicodeEncodeError: charmap\n'
        )
        msg, _, line_num = error_translator.explain_python_error(tb)
        self.assertEqual(line_num, 2)
        self.assertIn("dong 2", msg)

        try:
            transpiler.transpile_vpy_to_py('in("chua dong ngoac\n')
        except Exception as exc:
            t_msg, t_hint, t_line = error_translator.explain_transpile_error(exc)
            self.assertEqual(t_line, 1)
            self.assertIn("dong 1", t_msg)
            self.assertTrue(len(t_hint) > 0)

    def test_ide_intellisense(self) -> None:
        import tkinter as tk
        from vpy import ide

        root = tk.Tk()
        try:
            app = ide.VPyIDE(root)
            app.editor.delete("1.0", tk.END)
            app.editor.insert(
                "1.0",
                'ham tinh_tong(a, b):\n'
                '    trave a + b\n'
                'but = turtle.Turtle()\n'
                'but.\n'
                'random.\n'
                'dso\n'
                '"nh\n'
                'ti\n',
            )
            # 1. Goi y thuoc tinh cua doi tuong turtle (but.)
            app.editor.mark_set(tk.INSERT, "4.4")
            root.update()
            app._update_autocomplete()
            self.assertTrue(any(m[0] == "forward" for m in app._ac_matches))

            # 2. Goi y thuoc tinh cua thu vien (random.)
            app.editor.mark_set(tk.INSERT, "5.7")
            root.update()
            app._update_autocomplete()
            self.assertTrue(any(m[0] == "randint" for m in app._ac_matches))

            # 3. Fuzzy matching (dso -> dayso)
            app.editor.mark_set(tk.INSERT, "6.3")
            root.update()
            app._update_autocomplete()
            self.assertTrue(any(m[0] == "dayso" for m in app._ac_matches))

            # 4. Khong goi y ben trong chuoi ("nh)
            app.editor.mark_set(tk.INSERT, "7.3")
            root.update()
            app._update_autocomplete()
            self.assertEqual(len(app._ac_matches), 0)

            # 5. Goi y ham do nguoi dung tu viet (tinh_tong)
            app.editor.mark_set(tk.INSERT, "8.2")
            root.update()
            app._update_autocomplete()
            self.assertTrue(any(m[0] == "tinh_tong" for m in app._ac_matches))

            # 6. Emmet: go dung 'in' van hien goi y in("$0")
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "    in")
            app.editor.mark_set(tk.INSERT, "1.6")
            root.update()
            app._update_autocomplete()
            self.assertTrue(any(m[0] == "in" for m in app._ac_matches))

            # 7. Emmet nhieu dong giu thut le (neu-nguoclai) + go 1 ky tu da hien
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "    n")
            app.editor.mark_set(tk.INSERT, "1.5")
            root.update()
            app._update_autocomplete()
            names_1char = [m[0] for m in app._ac_matches]
            self.assertIn("neu", names_1char)
            self.assertIn("neu-nguoclai", names_1char)

            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "    neu-nguoclai")
            app.editor.mark_set(tk.INSERT, "1.16")
            root.update()
            app._update_autocomplete()
            app._accept_autocomplete()
            content = app.editor.get("1.0", "end-1c")
            self.assertIn("    neu :\n        \n    nguoclai:\n        ", content)
        finally:
            root.destroy()

    def test_ide_two_way_mode_switch(self) -> None:
        import tkinter as tk
        from vpy import ide

        root = tk.Tk()
        try:
            app = ide.VPyIDE(root)
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", 'ten = nhap("Ten: ")\nin(ten)\n')
            app.mode_var.set(".py")
            app._on_mode_change()
            py_text = app.editor.get("1.0", "end-1c")
            self.assertIn("input", py_text)
            self.assertIn("print", py_text)

            app.mode_var.set(".vpy")
            app._on_mode_change()
            vpy_text = app.editor.get("1.0", "end-1c")
            self.assertIn("nhap", vpy_text)
            self.assertIn("in", vpy_text)
        finally:
            root.destroy()

    def test_vhtml_vcss_transpile_and_ide_switch(self) -> None:
        import tkinter as tk
        from vpy import ide, web_transpiler

        vhtml_src = (
            '<hop lop="the">\n'
            '    <kieu>\n'
            '        tieude { mau-chu: red; can-le: giua; }\n'
            '    </kieu>\n'
            '    <tieude>Xin chao</tieude>\n'
            '    <nut>Bam</nut>\n'
            '</hop>\n'
        )
        html_out = web_transpiler.transpile_vhtml_to_html(vhtml_src)
        self.assertIn('<div class="the">', html_out)
        self.assertIn("<style>", html_out)
        self.assertIn("color: red;", html_out)
        self.assertIn("text-align: center;", html_out)
        self.assertIn("<h1>Xin chao</h1>", html_out)
        self.assertIn("<button>Bam</button>", html_out)

        roundtrip = web_transpiler.transpile_html_to_vhtml(html_out)
        self.assertIn('<hop lop="the">', roundtrip)
        self.assertIn("mau-chu: do;", roundtrip)
        self.assertIn("Xin chao</tieude", roundtrip)

        root = tk.Tk()
        try:
            app = ide.VPyIDE(root)
            app._load_lesson("5. Trang web dau tien (.vhtml)")
            self.assertEqual(app.mode_var.get(), ".vhtml")
            app.mode_var.set(".html")
            app._on_mode_change()
            self.assertIn("<h1>", app.editor.get("1.0", tk.END))
        finally:
            root.destroy()

    def test_file_extension_context_autocomplete(self) -> None:
        from vpy import intellisense

        # 1. Ngoai <kieu> trong .vhtml -> goi y the HTML tieng Viet (tieude1 -> tieude6)
        m_tag, _ = intellisense.get_completions("<than>\n    ti", "    ti", ".vhtml", text_before_cursor="<than>\n    ti")
        self.assertTrue(any(x[0] == "tieude1" for x in m_tag))
        self.assertTrue(any(x[0] == "tieude6" for x in m_tag))
        self.assertFalse(any(x[0] == "mau-chu" for x in m_tag))

        # 2. Ben trong <kieu>...</kieu> trong .vhtml -> goi y CSS tieng Viet
        vhtml_css_ctx = "<kieu>\n    than { ma"
        m_css, _ = intellisense.get_completions(vhtml_css_ctx, "    than { ma", ".vhtml", text_before_cursor=vhtml_css_ctx)
        self.assertTrue(any(x[0] == "mau-chu" for x in m_css))

        # 3. Ben trong the mo <hop  trong .vhtml -> goi y thuoc tinh
        attr_ctx = "<hop lo"
        m_attr, _ = intellisense.get_completions(attr_ctx, "<hop lo", ".vhtml", text_before_cursor=attr_ctx)
        self.assertTrue(any(x[0] == "lop" for x in m_attr))

        # 4. File .css -> goi y CSS chuan
        m_plain_css, _ = intellisense.get_completions("body { col", "body { col", ".css", text_before_cursor="body { col")
        self.assertTrue(any(x[0] == "color" for x in m_plain_css))

        # 5. File .html go '<t' -> goi y title, table... va word_col=0 de khong bi du '<<'
        m_html_t, col_t = intellisense.get_completions("<t", "<t", ".html", text_before_cursor="<t")
        self.assertEqual(col_t, 0)
        self.assertTrue(any(x[0] == "title" for x in m_html_t))
        self.assertTrue(any(x[0] == "table" for x in m_html_t))

    def test_auto_detect_code_mode(self) -> None:
        from vpy import intellisense

        self.assertEqual(intellisense.detect_code_mode(""), ".vpy")
        self.assertEqual(intellisense.detect_code_mode('in("Xin chao")'), ".vpy")
        self.assertEqual(intellisense.detect_code_mode('print("Hello")'), ".py")
        self.assertEqual(intellisense.detect_code_mode("<tieude>Chao</tieude>"), ".vhtml")
        self.assertEqual(intellisense.detect_code_mode("<h1>Hello</h1>"), ".html")
        self.assertEqual(intellisense.detect_code_mode("than { mau-chu: red; }"), ".vcss")
        self.assertEqual(intellisense.detect_code_mode("body { color: red; }"), ".css")

    def test_ide_editing_ergonomics(self) -> None:
        import tkinter as tk
        from vpy import ide

        root = tk.Tk()
        try:
            app = ide.VPyIDE(root)
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", 'in("a")\nin("b")\n')

            # 1. Ctrl+/ comment va bo comment nhieu dong
            app.editor.tag_add(tk.SEL, "1.0", "2.7")
            app.toggle_comment()
            self.assertIn('# in("a")\n# in("b")', app.editor.get("1.0", tk.END))
            app.editor.tag_add(tk.SEL, "1.0", "2.9")
            app.toggle_comment()
            self.assertIn('in("a")\nin("b")', app.editor.get("1.0", tk.END))

            # 2. Shift+Tab giam thut le
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "    x = 1\n")
            app.editor.mark_set(tk.INSERT, "1.5")
            app._on_shift_tab()
            self.assertTrue(app.editor.get("1.0", "1.end") == "x = 1")

            # 3. Tim kiem (Ctrl+F)
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", 'ten = "An"\nin(ten)\n')
            app.find_entry.insert(0, "ten")
            app.find_next()
            self.assertTrue(len(app.editor.tag_ranges("find_match")) >= 2)

            # 4. Highlight cap ngoac tuong ung
            app.editor.mark_set(tk.INSERT, "2.2")
            app._highlight_matching_brace()
            self.assertEqual(len(app.editor.tag_ranges("brace_match")), 4)
        finally:
            root.destroy()

    def test_transpiler_preserves_dot_attributes(self) -> None:
        src_py = "print(event.type, obj.set(1), item.round())\n"
        vpy_code = transpiler.transpile_py_to_vpy(src_py)
        self.assertIn("event.type", vpy_code)
        self.assertIn("obj.set", vpy_code)
        self.assertIn("item.round", vpy_code)
        self.assertIn("in(", vpy_code)

        back_py = transpiler.transpile_vpy_to_py("in(event.type, obj.set(1))\n")
        self.assertIn("event.type", back_py)
        self.assertIn("obj.set", back_py)
        self.assertIn("print(", back_py)

    def test_open_and_save_defaults_to_vietnamese(self) -> None:
        import tkinter as tk
        from vpy import ide, web_transpiler

        with tempfile.TemporaryDirectory() as tmp:
            py_file = Path(tmp) / "demo.py"
            py_file.write_text('print(abs(-5))\n', encoding="utf-8")

            html_file = Path(tmp) / "index.html"
            html_file.write_text('<table><tr><td>Xin chao</td></tr></table>\n', encoding="utf-8")

            css_file = Path(tmp) / "style.css"
            css_file.write_text('button { cursor: pointer; font-weight: bold; }\n', encoding="utf-8")

            root = tk.Tk()
            try:
                app = ide.VPyIDE(root)
                # 1. Mo .py -> hien thi tieng Viet (.vpy)
                app.load_file(py_file)
                self.assertEqual(app.mode_var.get(), ".vpy")
                self.assertIn("in(tuyetdoi(-5))", app.editor.get("1.0", tk.END))
                app.save_file()
                self.assertIn("print(abs(-5))", py_file.read_text(encoding="utf-8"))

                # 2. Mo .html -> hien thi tieng Viet (.vhtml)
                app.load_file(html_file)
                self.assertEqual(app.mode_var.get(), ".vhtml")
                self.assertIn("<bang><hang><o_bang>Xin chao</o_bang></hang></bang>", app.editor.get("1.0", tk.END))
                app.save_file()
                self.assertIn("<table><tr><td>Xin chao</td></tr></table>", html_file.read_text(encoding="utf-8"))

                # 3. Mo .css -> hien thi tieng Viet (.vcss)
                app.load_file(css_file)
                self.assertEqual(app.mode_var.get(), ".vcss")
                vcss_txt = app.editor.get("1.0", tk.END)
                self.assertIn("con-tro: ban-tay;", vcss_txt)
                self.assertIn("do-dam: dam;", vcss_txt)
            finally:
                root.destroy()

    def test_realtime_diagnostics_and_format_code(self) -> None:
        import tkinter as tk
        from vpy import ide

        root = tk.Tk()
        try:
            app = ide.VPyIDE(root)
            # 1. Real-time diagnostics cho .vpy thieu dau ':'
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "neu x > 1\n    in(x)\n")
            app._on_editor_change()
            err = app._run_diagnostics()
            self.assertIsNotNone(err)
            self.assertTrue(len(app.editor.tag_ranges("lint_err")) >= 2)

            # 2. Real-time diagnostics cho .vhtml chua dong the
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "<hop>\n<tieude>Chao</tieude>\n")
            app._on_editor_change()
            err_html = app._run_diagnostics()
            self.assertIsNotNone(err_html)
            self.assertIn("hop", err_html)

            # 3. Format code .vhtml tu can le 4 dau cach
            app.editor.delete("1.0", tk.END)
            app.editor.insert("1.0", "<hop>\n<tieude>Chao</tieude>\n<doan>Ok</doan>\n</hop>\n")
            app._on_editor_change()
            app.format_code()
            formatted = app.editor.get("1.0", "end-1c")
            self.assertIn("<hop>\n    <tieude>Chao</tieude>\n    <doan>Ok</doan>\n</hop>", formatted)
        finally:
            root.destroy()

    def test_vietnamese_colors_and_css_link(self) -> None:
        from vpy import intellisense, web_transpiler

        vcss = "tieude1 {\n    mau-nen: cam;\n    mau-chu: xanh-la;\n}\n"
        css = web_transpiler.transpile_vcss_to_css(vcss)
        self.assertIn("h1 {", css)
        self.assertIn("background-color: orange;", css)
        self.assertIn("color: green;", css)

        back_vcss = web_transpiler.transpile_css_to_vcss(css)
        self.assertIn("mau-nen: cam;", back_vcss)
        self.assertIn("mau-chu: xanh-la;", back_vcss)

        vhtml = '<dau><lienket_css file="test.css"></dau>\n'
        html = web_transpiler.transpile_vhtml_to_html(vhtml)
        self.assertIn('<link rel="stylesheet" href="test.css">', html)
        self.assertIn('<lienket_css file="test.css">', web_transpiler.transpile_html_to_vhtml(html))

        m_col, _ = intellisense.get_completions("    mau-nen: ca", "    mau-nen: ca", ".vcss", text_before_cursor="    mau-nen: ca")
        self.assertTrue(any(x[0] == "cam" for x in m_col))

    def test_live_reload_server_on_save(self) -> None:
        import tkinter as tk
        import urllib.request
        from unittest import mock
        from vpy import ide

        with tempfile.TemporaryDirectory() as tmp:
            html_file = Path(tmp) / "index.html"
            html_file.write_text('<h1>Xin chao</h1>\n', encoding="utf-8")
            css_file = Path(tmp) / "style.css"
            css_file.write_text('h1 { color: red; }\n', encoding="utf-8")

            root = tk.Tk()
            try:
                app = ide.VPyIDE(root)
                app.load_file(html_file)
                with mock.patch("webbrowser.open") as m_open:
                    app.run_code()
                self.assertTrue(m_open.called)
                self.assertIsNotNone(app._live_port)

                base_url = f"http://127.0.0.1:{app._live_port}"
                v1 = urllib.request.urlopen(f"{base_url}/__vide_version").read().decode("utf-8")
                preview_html = urllib.request.urlopen(f"{base_url}/_vide_preview.html").read().decode("utf-8")
                self.assertIn("/__vide_version", preview_html)

                # Chuyen sang tab CSS, sua mau va luu -> version phai tang tu dong
                app.load_file(css_file)
                app.editor.delete("1.0", tk.END)
                app.editor.insert("1.0", "tieude1 { mau-chu: cam; }\n")
                app.save_file()

                v2 = urllib.request.urlopen(f"{base_url}/__vide_version").read().decode("utf-8")
                self.assertNotEqual(v1, v2)
                self.assertIn("color: orange;", css_file.read_text(encoding="utf-8"))
            finally:
                if getattr(app, "_live_server", None) is not None:
                    app._live_server.shutdown()
                    app._live_server.server_close()
                    app._live_server = None
                root.destroy()

    def test_vietnamese_js_transpiler_and_ide(self) -> None:
        from vpy import intellisense, js_transpiler, web_transpiler

        vjs = (
            'bien solan = 0;\n'
            'ham bam_nut() {\n'
            '    neu (solan == 0) {\n'
            '        ghilog("neu bien khong doi");\n'
            '    } hoacla (solan > 0) {\n'
            '        tim_ma("tieude").noidung = "OK";\n'
            '    } nguoclai {\n'
            '        thongbao("Xong");\n'
            '    }\n'
            '}\n'
        )
        js = js_transpiler.transpile_vjs_to_js(vjs)
        self.assertIn("let solan = 0;", js)
        self.assertIn("function bam_nut()", js)
        self.assertIn("else if (solan > 0)", js)
        self.assertIn('console.log("neu bien khong doi")', js)
        self.assertIn('document.getElementById("tieude").textContent = "OK";', js)
        self.assertIn('alert("Xong")', js)

        vjs_back = js_transpiler.transpile_js_to_vjs(js)
        self.assertIn("bien solan = 0;", vjs_back)
        self.assertIn("hoacla (solan > 0)", vjs_back)
        self.assertIn('tim_ma("tieude").noidung = "OK";', vjs_back)

        self.assertEqual(intellisense.detect_code_mode('bien x = 10;\nghilog(x);'), ".vjs")
        self.assertEqual(intellisense.detect_code_mode('let x = 10;\nconsole.log(x);'), ".js")

        vhtml_js = '<dau><lienket_js file="app.js"></dau><than><kichban>bien a = 1;</kichban></than>'
        html_js = web_transpiler.transpile_vhtml_to_html(vhtml_js)
        self.assertIn('<script src="app.js"></script>', html_js)
        self.assertIn('<script>let a = 1;</script>', html_js)


if __name__ == "__main__":
    unittest.main()
