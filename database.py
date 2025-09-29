import sqlite3
import json
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="transcripts.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create transcripts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_text TEXT NOT NULL,
                agent_names TEXT,
                patient_names TEXT,
                test_centers TEXT,
                tests_mentioned TEXT,
                doctors_mentioned TEXT,
                contact_info TEXT,
                appointment_dates TEXT,
                departments TEXT,
                sentiment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create qa_evaluations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript_id INTEGER NOT NULL,
                transcript_summary TEXT,
                greeting_data TEXT NOT NULL,
                information_data TEXT NOT NULL,
                hold_procedure_data TEXT NOT NULL,
                quality_check_data TEXT NOT NULL,
                unsure_situation_data TEXT NOT NULL,
                closing_script_data TEXT NOT NULL,
                sound_quality_data TEXT NOT NULL,
                record_handling_data TEXT NOT NULL,
                total_score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transcript_id) REFERENCES transcripts (id)
            )
        ''')

        conn.commit()
        conn.close()

    def save_transcript_data(self, filename, original_text, extracted_fields):
        """Save transcript and extracted data to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Convert lists to JSON strings for storage
            agent_names_json = json.dumps(extracted_fields.get('agent_names', []))
            patient_names_json = json.dumps(extracted_fields.get('patient_names', []))
            test_centers_json = json.dumps(extracted_fields.get('test_centers', []))
            tests_mentioned_json = json.dumps(extracted_fields.get('tests_mentioned', []))
            doctors_mentioned_json = json.dumps(extracted_fields.get('doctors_mentioned', []))
            contact_info_json = json.dumps(extracted_fields.get('contact_info', []))
            appointment_dates_json = json.dumps(extracted_fields.get('appointment_dates', []))
            departments_json = json.dumps(extracted_fields.get('departments', []))
            sentiment_json=json.dumps(extracted_fields.get('sentiment',[]))
            print((filename, original_text, agent_names_json, patient_names_json, test_centers_json,
                  tests_mentioned_json, doctors_mentioned_json, contact_info_json,
                  appointment_dates_json, departments_json,sentiment_json))
            cursor.execute('''
                INSERT INTO transcripts
                (filename, original_text, agent_names, patient_names, test_centers,
                 tests_mentioned, doctors_mentioned, contact_info, appointment_dates, departments,sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
            ''', (filename, original_text, agent_names_json, patient_names_json, test_centers_json,
                  tests_mentioned_json, doctors_mentioned_json, contact_info_json,
                  appointment_dates_json, departments_json,sentiment_json))

            transcript_id = cursor.lastrowid
            conn.commit()
            return transcript_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

    def get_transcript_by_id(self, transcript_id):
        """Retrieve transcript data by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, filename, original_text, agent_names, patient_names, test_centers,
                       tests_mentioned, doctors_mentioned, contact_info, appointment_dates,
                       departments,sentiment,created_at
                FROM transcripts WHERE id = ?
            ''', (transcript_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'filename': result[1],
                    'original_text': result[2],
                    'agent_names': json.loads(result[3]) if result[3] else [],
                    'patient_names': json.loads(result[4]) if result[4] else [],
                    'test_centers': json.loads(result[5]) if result[5] else [],
                    'tests_mentioned': json.loads(result[6]) if result[6] else [],
                    'doctors_mentioned': json.loads(result[7]) if result[7] else [],
                    'contact_info': json.loads(result[8]) if result[8] else [],
                    'appointment_dates': json.loads(result[9]) if result[9] else [],
                    'departments': json.loads(result[10]) if result[10] else [],
                    'sentiment':json.loads(result[11]) if result[11] else [],
                    'created_at': result[12]
                }
            return None

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

    def get_all_transcripts(self):
        """Retrieve all transcripts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, filename, created_at
                FROM transcripts ORDER BY created_at DESC
            ''')

            results = cursor.fetchall()
            transcripts = []
            for result in results:
                transcripts.append({
                    'id': result[0],
                    'filename': result[1],
                    'created_at': result[2]
                })
            return transcripts

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

    def save_qa_evaluation(self, transcript_id, qa_evaluation_dict):
        """Save QA evaluation data to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Convert sections to JSON strings
            greeting_json = json.dumps(qa_evaluation_dict.get('greeting', {}))
            information_json = json.dumps(qa_evaluation_dict.get('information', {}))
            hold_procedure_json = json.dumps(qa_evaluation_dict.get('hold_procedure', {}))
            quality_check_json = json.dumps(qa_evaluation_dict.get('quality_check', {}))
            unsure_situation_json = json.dumps(qa_evaluation_dict.get('unsure_situation', {}))
            closing_script_json = json.dumps(qa_evaluation_dict.get('closing_script', {}))
            sound_quality_json = json.dumps(qa_evaluation_dict.get('sound_quality', {}))
            record_handling_json = json.dumps(qa_evaluation_dict.get('record_handling', {}))

            cursor.execute('''
                INSERT INTO qa_evaluations
                (transcript_id, transcript_summary, greeting_data, information_data,
                 hold_procedure_data, quality_check_data, unsure_situation_data,
                 closing_script_data, sound_quality_data, record_handling_data, total_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (transcript_id, qa_evaluation_dict.get('transcript_summary'),
                  greeting_json, information_json, hold_procedure_json,
                  quality_check_json, unsure_situation_json, closing_script_json,
                  sound_quality_json, record_handling_json,
                  qa_evaluation_dict.get('total_score', 0)))

            qa_evaluation_id = cursor.lastrowid
            conn.commit()
            return qa_evaluation_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

    def get_qa_evaluation_by_transcript_id(self, transcript_id):
        """Retrieve QA evaluation by transcript ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, transcript_id, transcript_summary, greeting_data,
                       information_data, hold_procedure_data, quality_check_data,
                       unsure_situation_data, closing_script_data, sound_quality_data,
                       record_handling_data, total_score, created_at
                FROM qa_evaluations WHERE transcript_id = ?
            ''', (transcript_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'transcript_id': result[1],
                    'transcript_summary': result[2],
                    'greeting': json.loads(result[3]) if result[3] else {},
                    'information': json.loads(result[4]) if result[4] else {},
                    'hold_procedure': json.loads(result[5]) if result[5] else {},
                    'quality_check': json.loads(result[6]) if result[6] else {},
                    'unsure_situation': json.loads(result[7]) if result[7] else {},
                    'closing_script': json.loads(result[8]) if result[8] else {},
                    'sound_quality': json.loads(result[9]) if result[9] else {},
                    'record_handling': json.loads(result[10]) if result[10] else {},
                    'total_score': result[11],
                    'created_at': result[12]
                }
            return None

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

    def get_qa_evaluation_by_id(self, qa_evaluation_id):
        """Retrieve QA evaluation by QA evaluation ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, transcript_id, transcript_summary, greeting_data,
                       information_data, hold_procedure_data, quality_check_data,
                       unsure_situation_data, closing_script_data, sound_quality_data,
                       record_handling_data, total_score, created_at
                FROM qa_evaluations WHERE id = ?
            ''', (qa_evaluation_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'transcript_id': result[1],
                    'transcript_summary': result[2],
                    'greeting': json.loads(result[3]) if result[3] else {},
                    'information': json.loads(result[4]) if result[4] else {},
                    'hold_procedure': json.loads(result[5]) if result[5] else {},
                    'quality_check': json.loads(result[6]) if result[6] else {},
                    'unsure_situation': json.loads(result[7]) if result[7] else {},
                    'closing_script': json.loads(result[8]) if result[8] else {},
                    'sound_quality': json.loads(result[9]) if result[9] else {},
                    'record_handling': json.loads(result[10]) if result[10] else {},
                    'total_score': result[11],
                    'created_at': result[12]
                }
            return None

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()

    def get_all_qa_evaluations(self):
        """Retrieve all QA evaluations with transcript info."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT qa.id, qa.transcript_id, t.filename, qa.total_score, qa.created_at,
                       t.agent_names, t.patient_names, t.test_centers
                FROM qa_evaluations qa
                JOIN transcripts t ON qa.transcript_id = t.id
                ORDER BY qa.created_at DESC
            ''')

            results = cursor.fetchall()
            evaluations = []
            for result in results:
                evaluations.append({
                    'qa_id': result[0],
                    'transcript_id': result[1],
                    'filename': result[2],
                    'total_score': result[3],
                    'created_at': result[4],
                    'agent_names': json.loads(result[5]) if result[5] else [],
                    'patient_names': json.loads(result[6]) if result[6] else [],
                    'test_centers': json.loads(result[7]) if result[7] else []
                })
            return evaluations

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            conn.close()