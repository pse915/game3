import json, tempfile, unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from engine import new_state
from storage import LocalStore, SheetsStore, StorageError, make_store

class StorageConcurrencyTests(unittest.TestCase):
    def test_10_20_30_isolated_students_save_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            store=LocalStore(Path(d)/'class.sqlite3')
            for count in (10,20,30):
                states=[new_state('QA-'+str(count),str(i),'가상') for i in range(count)]
                with ThreadPoolExecutor(max_workers=count) as pool:list(pool.map(store.save,states))
                for s in states:self.assertEqual(store.load(s['class_code'],s['student_id']),s)
            self.assertEqual(len(store.all_latest()),60)

    def test_late_older_revision_cannot_roll_back_current_run(self):
        with tempfile.TemporaryDirectory() as d:
            store=LocalStore(Path(d)/'class.sqlite3');s=new_state('QA','01','가상')
            newest={**s,'revision':3};store.save(newest);store.save(s);store.save(newest)
            self.assertEqual(store.load('QA','01')['revision'],3)
            self.assertEqual(store.all_latest()[0]['revision'],3)

    def test_sheets_duplicate_and_out_of_order_snapshots(self):
        s=new_state('QA','01','가상');latest={**s,'revision':2}
        rows=[{'run_id':s['run_id'],'revision':str(x['revision']),'class_code':'QA','student_id':'01','state_json':json.dumps(x)} for x in (latest,s,latest,s)]
        class FakeTab:
            def get_all_records(self,**kwargs):return rows
        store=SheetsStore.__new__(SheetsStore);store.tab=FakeTab()
        self.assertEqual(store.load('QA','01')['revision'],2)
        self.assertEqual(store.all_latest()[0]['revision'],2)

    def test_partial_google_configuration_does_not_silently_switch_storage(self):
        for cfg in ({'sheet_id':'example'},{'gcp_service_account':{'x':1}}):
            with self.assertRaises(StorageError):make_store(cfg)

if __name__=='__main__':unittest.main()
