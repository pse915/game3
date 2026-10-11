"""Streamlit integration with the real reducer/store and a component message bridge.
Browser transport and live Google APIs are covered separately or marked unverified.
"""
import asyncio, os, tempfile, unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch, MagicMock
import streamlit as st
from streamlit.testing.v1 import AppTest
from content import EVENTS, REQUIRED

ROOT=Path(__file__).resolve().parents[1]

class HostIntegrationTests(unittest.TestCase):
    def test_login_complete_story_reflection_and_teacher_dashboard(self):
        with tempfile.TemporaryDirectory() as d:
            bridge={}
            def component(**kwargs):return bridge.pop('message',None)
            loop=MagicMock(spec=asyncio.AbstractEventLoop)
            loop.is_closed.return_value=False
            loop.is_running.return_value=False
            # AppTest only installs the loop; this app has no asyncio work.
            # A socket-free loop placeholder is opt-in for network-restricted QA.
            loop_patch=patch('asyncio.new_event_loop',return_value=loop) if os.getenv('QA_FAKE_EVENT_LOOP')=='1' else nullcontext()
            with loop_patch,patch('storage.DB_PATH',Path(d)/'host.sqlite3'),patch.dict(os.environ,{'SEWOL_DB':str(Path(d)/'host.sqlite3'),'TEACHER_PASSWORD':'QA-Teacher-2026'}),patch('streamlit.components.v1.declare_component',return_value=component):
                st.cache_resource.clear()
                app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20).run()
                self.assertFalse(app.exception)
                for widget,value in zip(app.text_input,['QA','01','<b>가상</b>','qa-password-2026']):widget.set_value(value)
                app.button[0].click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state['world_state']['stage'],0)
                self.assertTrue(any('&lt;b&gt;' in x.value for x in app.markdown))
                def message(kind,**extra):
                    state=app.session_state['world_state'];rev=state['revision']
                    bridge['message']={'type':kind,'nonce':f'host-{rev}',**extra}
                    app.run()
                    self.assertFalse(app.exception)
                    self.assertEqual(app.session_state['world_state']['revision'],rev+1)
                for stage in range(3):
                    for event in REQUIRED[stage]:message('choose',event_id=event,choice_id=next(iter(EVENTS[event]['choices'])))
                    message('finish' if stage==2 else 'advance')
                self.assertTrue(app.session_state['world_state']['ended'])
                self.assertEqual(len(app.text_area),1)
                app.text_area[0].set_value('돌봄 인력과 재정이 필요하다. 나도 건강과 일을 준비하고 싶다.')
                next(b for b in app.button if b.label=='소감 저장').click().run()
                self.assertFalse(app.exception)
                self.assertIn('돌봄 인력',app.session_state['world_state']['reflection'])
                # Actual app storage is read by the teacher view, not a fabricated table.
                app.query_params['mode']='teacher';app.run()
                app.text_input[0].set_value('QA-Teacher-2026').run()
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value,'1')
                self.assertEqual(app.metric[1].value,'1')
                self.assertGreaterEqual(len(app.dataframe),1)
                st.cache_resource.clear()

if __name__=='__main__':unittest.main()
