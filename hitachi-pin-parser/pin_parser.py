#!/usr/bin/env python3
"""
PIN Notification Parser
Parses HR PIN notification emails from MinIO, processes with Azure OpenAI,
and generates Excel report with pin_monitoring_table and employee_stories_table.
"""

import os
import sys
import json
import re
from datetime import datetime
from io import BytesIO
import email
from email import policy
from typing import List, Dict, Any
import traceback

import pandas as pd
from minio import Minio
from minio.error import S3Error
import requests


class PINParser:
    def __init__(self):
        """Initialize the PIN Parser with configuration from environment variables."""
        # MinIO Configuration
        self.minio_endpoint = os.getenv('MINIO_ENDPOINT', 'minio.hyperplane-minio.svc.cluster.local:9000')
        self.minio_access_key = os.getenv('MINIO_ACCESS_KEY')
        self.minio_secret_key = os.getenv('MINIO_SECRET_KEY')
        self.input_bucket = os.getenv('MINIO_INPUT_BUCKET', 'hitachi-pin-input')
        self.output_bucket = os.getenv('MINIO_OUTPUT_BUCKET', 'hitachi-pin-output')
        
        # Azure OpenAI Configuration
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_api_key = os.getenv('AZURE_OPENAI_KEY')
        
        # Validate configuration
        if not all([self.minio_access_key, self.minio_secret_key]):
            raise ValueError("MinIO credentials not found in environment variables")
        if not all([self.azure_endpoint, self.azure_api_key]):
            raise ValueError("Azure OpenAI credentials not found in environment variables")
        
        # Initialize MinIO client
        self.minio_client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=False  # Using HTTP inside k8s cluster
        )
        
        print(f"Initialized MinIO client with endpoint: {self.minio_endpoint}")
        print(f"Input bucket: {self.input_bucket}")
        print(f"Output bucket: {self.output_bucket}")
    
    def parse_email_content(self, email_data: bytes) -> Dict[str, Any]:
        """Parse email data and extract relevant information."""
        try:
            msg = email.message_from_bytes(email_data, policy=policy.default)
            
            # Extract subject
            subject = msg.get('subject', '')
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')
                                break
                        except:
                            continue
            else:
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                except:
                    body = str(msg.get_payload())
            
            return {
                'subject': subject,
                'body': body,
                'from': msg.get('from', ''),
                'date': msg.get('date', '')
            }
        except Exception as e:
            print(f"Error parsing email: {e}")
            traceback.print_exc()
            return {'subject': '', 'body': '', 'from': '', 'date': ''}
    
    def extract_info_with_openai(self, email_content: Dict[str, Any]) -> Dict[str, Any]:
        """Use Azure OpenAI to extract structured information from email."""
        subject = email_content.get('subject', '')
        body = email_content.get('body', '')
        
        prompt = f"""You are an HR data extraction assistant. Extract the following information from this PIN notification email and return it as a JSON object.

Email Subject: {subject}

Email Body:
{body}

Please extract and return ONLY a valid JSON object with these exact fields:
{{
    "pin_action": "The type of action (e.g., 'Departure', 'New Hire', 'Going on Leave', 'Transfer – Move to Another Manager', 'Contract Extension for Contingent Worker', 'Detail Change')",
    "effective_date": "The effective date in YYYY-MM-DD format",
    "employee_tgi": "Employee TGI/SGI number (e.g., T0074074, S0153511)",
    "employee_name": "Full employee name",
    "cost_center": "Cost center code and name",
    "manager": "Manager name and TGI",
    "business_title": "Job title",
    "employee_type": "Employee type (e.g., Contingent, Permanent)",
    "summary": "Brief summary of the change (1-2 sentences)"
}}

Return ONLY the JSON object, no additional text or markdown formatting.
"""
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.azure_api_key
            }
            
            payload = {
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a precise data extraction assistant. Always return valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 1000
            }
            
            response = requests.post(
                self.azure_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    content = re.sub(r'^```json\s*\n', '', content)
                    content = re.sub(r'\n```$', '', content)
                
                extracted_data = json.loads(content)
                return extracted_data
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                return self.fallback_extraction(email_content)
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            traceback.print_exc()
            return self.fallback_extraction(email_content)
    
    def fallback_extraction(self, email_content: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method using regex to extract information."""
        subject = email_content.get('subject', '')
        body = email_content.get('body', '')
        
        # Extract action type from subject
        action = "Unknown"
        if "DEPARTURE" in subject.upper():
            action = "Departure"
        elif "NEW HIRE" in subject.upper():
            action = "New Hire"
        elif "GOING ON LEAVE" in subject.upper():
            action = "Going on Leave"
        elif "DETAIL CHANGE" in subject.upper():
            action = "Detail Change"
        
        # Extract employee name and TGI from subject
        # Pattern: Name (TGI)
        name_match = re.search(r':\s*([^(]+)\s*\(([ST]\d+)\)', subject)
        employee_name = name_match.group(1).strip() if name_match else ""
        employee_tgi = name_match.group(2).strip() if name_match else ""
        
        # Extract effective date from subject (YYYY MM DD format)
        date_match = re.search(r'(\d{4})\s+(\d{2})\s+(\d{2})', subject)
        effective_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else ""
        
        # Extract other fields from body
        cost_center = ""
        manager = ""
        business_title = ""
        employee_type = ""
        
        # Look for cost center
        cc_match = re.search(r'Cost Center:([^\n]+)', body, re.IGNORECASE)
        if cc_match:
            cost_center = cc_match.group(1).strip()
        
        # Look for manager
        mgr_match = re.search(r'Manager:([^\n]+)', body, re.IGNORECASE)
        if mgr_match:
            manager = mgr_match.group(1).strip()
        
        # Look for business title
        title_match = re.search(r'Business Title:([^\n]+)', body, re.IGNORECASE)
        if title_match:
            business_title = title_match.group(1).strip()
        
        # Look for employee type
        type_match = re.search(r'Employee Type:([^\n]+)', body, re.IGNORECASE)
        if type_match:
            employee_type = type_match.group(1).strip()
        
        return {
            'pin_action': action,
            'effective_date': effective_date,
            'employee_tgi': employee_tgi,
            'employee_name': employee_name,
            'cost_center': cost_center,
            'manager': manager,
            'business_title': business_title,
            'employee_type': employee_type,
            'summary': f"{action} for {employee_name} effective {effective_date}"
        }
    
    def download_emails_from_minio(self) -> List[Dict[str, Any]]:
        """Download all email files from MinIO input bucket."""
        emails = []
        
        try:
            # Check if bucket exists
            if not self.minio_client.bucket_exists(self.input_bucket):
                print(f"Warning: Bucket {self.input_bucket} does not exist. Creating it...")
                self.minio_client.make_bucket(self.input_bucket)
                print(f"Created bucket: {self.input_bucket}")
                return emails
            
            # List all objects in the bucket
            objects = self.minio_client.list_objects(self.input_bucket, recursive=True)
            
            for obj in objects:
                if obj.object_name.endswith('.eml'):
                    print(f"Processing: {obj.object_name}")
                    try:
                        # Download the email file
                        response = self.minio_client.get_object(self.input_bucket, obj.object_name)
                        email_data = response.read()
                        response.close()
                        response.release_conn()
                        
                        # Parse email
                        parsed_email = self.parse_email_content(email_data)
                        parsed_email['filename'] = obj.object_name
                        
                        emails.append(parsed_email)
                    except S3Error as e:
                        print(f"Error downloading {obj.object_name}: {e}")
                        continue
                    except Exception as e:
                        print(f"Error processing {obj.object_name}: {e}")
                        traceback.print_exc()
                        continue
            
            print(f"Downloaded {len(emails)} emails from MinIO")
            return emails
            
        except Exception as e:
            print(f"Error accessing MinIO: {e}")
            traceback.print_exc()
            return emails
    
    def process_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process emails and extract structured data using OpenAI."""
        processed_data = []
        
        for idx, email_content in enumerate(emails, 1):
            print(f"Processing email {idx}/{len(emails)}: {email_content.get('filename', 'unknown')}")
            
            extracted = self.extract_info_with_openai(email_content)
            extracted['filename'] = email_content.get('filename', '')
            extracted['email_date'] = email_content.get('date', '')
            
            processed_data.append(extracted)
            print(f"  -> Extracted: {extracted.get('pin_action')} - {extracted.get('employee_name')}")
        
        return processed_data
    
    def create_pin_monitoring_table(self, processed_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create pin_monitoring_table from processed data."""
        records = []
        
        for data in processed_data:
            # Parse PIN date from email date or use current date
            pin_date = datetime.now().strftime('%Y-%m-%d')
            try:
                if data.get('email_date'):
                    # Try to parse the email date
                    from email.utils import parsedate_to_datetime
                    pin_date = parsedate_to_datetime(data['email_date']).strftime('%Y-%m-%d')
            except:
                pass
            
            record = {
                'PIN_Date': pin_date,
                'PIN_Action': data.get('pin_action', ''),
                'PIN_Effective_Date': data.get('effective_date', ''),
                'PIN_Employee_TGI': data.get('employee_tgi', ''),
                'PIN_Employee_Name': data.get('employee_name', ''),
                'PIN_Cost_Center': data.get('cost_center', ''),
                'PIN_Manager': data.get('manager', ''),
                'PIN_Change_Summary': data.get('summary', ''),
                'PIN_Change': f"{data.get('pin_action', '')} {data.get('employee_name', '')} ({data.get('employee_tgi', '')}) – Effective Date {data.get('effective_date', '')}"
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Sort by PIN_Date and PIN_Effective_Date
        if not df.empty:
            df = df.sort_values(by=['PIN_Date', 'PIN_Effective_Date'], ascending=[False, False])
        
        return df
    
    def create_employee_stories_table(self, processed_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create employee_stories_table from processed data."""
        # Group by employee
        employee_data = {}
        
        for data in processed_data:
            tgi = data.get('employee_tgi', '')
            name = data.get('employee_name', '')
            
            if not tgi or not name:
                continue
            
            key = (name, tgi)
            
            if key not in employee_data:
                employee_data[key] = {
                    'name': name,
                    'tgi': tgi,
                    'events': []
                }
            
            # Create event string
            pin_date = datetime.now().strftime('%Y-%m-%d')
            try:
                if data.get('email_date'):
                    from email.utils import parsedate_to_datetime
                    pin_date = parsedate_to_datetime(data['email_date']).strftime('%Y-%m-%d')
            except:
                pass
            
            event = f"PIN {pin_date} ({data.get('effective_date', '')}) – {data.get('summary', '')}"
            employee_data[key]['events'].append({
                'date': pin_date,
                'effective_date': data.get('effective_date', ''),
                'event': event,
                'action': data.get('pin_action', '')
            })
        
        # Create records
        records = []
        for key, emp_data in employee_data.items():
            # Sort events by date
            emp_data['events'].sort(key=lambda x: x['date'], reverse=True)
            
            # Create story string
            story = "; ".join([e['event'] for e in emp_data['events']])
            
            # Get most recent change
            recent_change = ""
            if emp_data['events']:
                recent_event = emp_data['events'][0]
                action = recent_event['action']
                eff_date = recent_event['effective_date']
                
                if "Departure" in action:
                    recent_change = f"PIN {recent_event['date']} – DEPARTURE ON {eff_date}"
                elif "New Hire" in action or "Hire" in action:
                    recent_change = f"PIN {recent_event['date']} – NEW HIRE START ON {eff_date}"
                elif "Leave" in action:
                    recent_change = f"PIN {recent_event['date']} – GOING ON LEAVE ON {eff_date}"
                elif "Transfer" in action or "Manager" in action:
                    recent_change = f"PIN {recent_event['date']} – NEW MANAGER ON {eff_date}"
                elif "Contract Extension" in action:
                    recent_change = f"PIN {recent_event['date']} – CONTRACT EXTENSION ON {eff_date}"
                else:
                    recent_change = f"PIN {recent_event['date']} – {action.upper()} ON {eff_date}"
            
            record = {
                'PIN_Employee_Name': emp_data['name'],
                'PIN_Employee_TGI': emp_data['tgi'],
                'Possible_Name_Match': '',
                'Story_of_the_Person': story,
                'Recent_Changes': recent_change
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Sort by employee name
        if not df.empty:
            df = df.sort_values(by='PIN_Employee_Name')
        
        return df
    
    def create_excel_report(self, pin_monitoring_df: pd.DataFrame, employee_stories_df: pd.DataFrame, output_filename: str) -> str:
        """Create Excel file with both tables."""
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                # Write pin_monitoring_table
                pin_monitoring_df.to_excel(writer, sheet_name='PIN Monitoring', index=False)
                
                # Write employee_stories_table
                employee_stories_df.to_excel(writer, sheet_name='Employee Stories', index=False)
            
            print(f"Excel report created: {output_filename}")
            return output_filename
        except Exception as e:
            print(f"Error creating Excel report: {e}")
            traceback.print_exc()
            raise
    
    def upload_to_minio(self, local_file: str, object_name: str):
        """Upload file to MinIO output bucket."""
        try:
            # Check if bucket exists, create if not
            if not self.minio_client.bucket_exists(self.output_bucket):
                print(f"Creating bucket: {self.output_bucket}")
                self.minio_client.make_bucket(self.output_bucket)
            
            # Upload file
            self.minio_client.fput_object(
                self.output_bucket,
                object_name,
                local_file
            )
            print(f"Uploaded {local_file} to MinIO bucket {self.output_bucket} as {object_name}")
        except Exception as e:
            print(f"Error uploading to MinIO: {e}")
            traceback.print_exc()
            raise
    
    def run(self, output_dir: str = '.'):
        """Main execution flow."""
        print("=" * 80)
        print("PIN Notification Parser")
        print("=" * 80)
        
        # Download emails from MinIO
        print("\n[1/5] Downloading emails from MinIO...")
        emails = self.download_emails_from_minio()
        
        if not emails:
            print("Warning: No emails found in MinIO bucket. Using local sample files...")
            # Fallback to local files
            import glob
            local_emails = glob.glob('/root/lost+found/hitachi-pin-parser/data/*.eml')
            emails = []
            for email_file in local_emails:
                with open(email_file, 'rb') as f:
                    email_data = f.read()
                parsed = self.parse_email_content(email_data)
                parsed['filename'] = os.path.basename(email_file)
                emails.append(parsed)
            print(f"Loaded {len(emails)} local email files")
        
        if not emails:
            print("Error: No emails to process")
            return None
        
        # Process emails with OpenAI
        print(f"\n[2/5] Processing {len(emails)} emails with Azure OpenAI...")
        processed_data = self.process_emails(emails)
        
        # Create pin_monitoring_table
        print("\n[3/5] Creating PIN Monitoring Table...")
        pin_monitoring_df = self.create_pin_monitoring_table(processed_data)
        print(f"Created table with {len(pin_monitoring_df)} rows")
        
        # Create employee_stories_table
        print("\n[4/5] Creating Employee Stories Table...")
        employee_stories_df = self.create_employee_stories_table(processed_data)
        print(f"Created table with {len(employee_stories_df)} rows")
        
        # Create Excel report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = os.path.join(output_dir, f'pin_report_{timestamp}.xlsx')
        
        print(f"\n[5/5] Creating Excel report: {output_filename}")
        self.create_excel_report(pin_monitoring_df, employee_stories_df, output_filename)
        
        # Upload to MinIO
        print(f"\n[6/6] Uploading report to MinIO...")
        try:
            self.upload_to_minio(output_filename, f'pin_report_{timestamp}.xlsx')
        except Exception as e:
            print(f"Warning: Could not upload to MinIO: {e}")
        
        print("\n" + "=" * 80)
        print("Processing Complete!")
        print(f"Output file: {output_filename}")
        print("=" * 80)
        
        return output_filename


def main():
    """Main entry point."""
    try:
        parser = PINParser()
        output_file = parser.run(output_dir='/root/lost+found/hitachi-pin-parser')
        
        if output_file:
            print(f"\n✓ Success! Report generated: {output_file}")
            return 0
        else:
            print("\n✗ Failed to generate report")
            return 1
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
