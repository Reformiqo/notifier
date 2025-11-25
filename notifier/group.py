import frappe
import requests
import json
import time
from typing import Dict, List, Optional
import frappe
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage, QuotedMessage
from frappe.utils.file_manager import save_file
from datetime import datetime



base_url = frappe.db.get_single_value("Evolution API Settings", "base_url")
api_token = frappe.db.get_single_value("Evolution API Settings", "api_token")

# Add these to your existing code
@frappe.whitelist(allow_guest=True)
def get_groups_with_contacts(instance):
    """Get groups with resolved participant phone numbers"""
    
    # Get basic group data
    groups_data = get_groups(instance)
    
    if not groups_data or 'message' not in groups_data:
        return groups_data
    
    # Resolve participant contacts
    for group in groups_data['message']:
        if 'participants' in group:
            resolved_participants = resolve_participants_contacts(instance, group['participants'])
            group['resolved_participants'] = resolved_participants
    
    return groups_data

@frappe.whitelist(allow_guest=True) 
def get_groups(instance):
    """Your existing function - kept as is"""
    url = f"{base_url}/group/fetchAllGroups/{instance}?getParticipants=true"
    
    headers = {
        "apikey": api_token,
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

def resolve_participants_contacts(instance: str, participants: List[Dict]) -> List[Dict]:
    """Resolve actual phone numbers for all participants"""
    resolved = []
    
    for participant in participants:
        resolved_participant = {
            'original_id': participant['id'],
            'admin': participant.get('admin'),
            'actual_phone': None,
            'type': None,
            'contact_name': None
        }
        
        if participant['id'].endswith('@s.whatsapp.net'):
            # Regular WhatsApp user
            resolved_participant['actual_phone'] = participant['id'].replace('@s.whatsapp.net', '')
            resolved_participant['type'] = 'regular'
            
        elif participant['id'].endswith('@lid'):
            # Linked device - try to get contact info
            contact_info = get_contact_info(instance, participant['id'])
            if contact_info:
                resolved_participant.update(contact_info)
            resolved_participant['type'] = 'business_linked'
        
        resolved.append(resolved_participant)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.1)
    
    return resolved

def get_contact_info(instance: str, participant_id: str) -> Optional[Dict]:
    """Get contact information for a participant ID"""
    
    # Method 1: Try fetchProfile endpoint
    contact_info = fetch_profile_info(instance, participant_id)
    if contact_info:
        return contact_info
    
    # Method 2: Try findContacts endpoint  
    contact_info = find_contact_info(instance, participant_id)
    if contact_info:
        return contact_info
        
    # Method 3: Try to extract number from @lid ID (sometimes works)
    extracted_number = extract_number_from_lid(participant_id)
    if extracted_number:
        return {
            'actual_phone': extracted_number,
            'contact_name': 'Extracted from ID'
        }
    
    return None

def fetch_profile_info(instance: str, participant_id: str) -> Optional[Dict]:
    """Try to fetch profile using Evolution API fetchProfile endpoint"""
    try:
        # Remove @lid suffix and try as phone number
        phone_candidate = participant_id.replace('@lid', '')
        
        url = f"{base_url}/chat/fetchProfile/{phone_candidate}"
        headers = {"apikey": api_token}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'actual_phone': data.get('phone') or phone_candidate,
                'contact_name': data.get('name') or data.get('pushName')
            }
            
    except Exception as e:
        frappe.log_error(f"Error in fetch_profile_info: {str(e)}")
    
    return None

def find_contact_info(instance: str, participant_id: str) -> Optional[Dict]:
    """Try to find contact using Evolution API findContacts endpoint"""
    try:
        url = f"{base_url}/chat/findContacts"
        headers = {
            "apikey": api_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "where": {
                "id": participant_id
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                contact = data[0]
                return {
                    'actual_phone': contact.get('phone') or contact.get('number'),
                    'contact_name': contact.get('pushName') or contact.get('name')
                }
                
    except Exception as e:
        frappe.log_error(f"Error in find_contact_info: {str(e)}")
    
    return None

def extract_number_from_lid(participant_id: str) -> Optional[str]:
    """Try to extract a valid phone number from @lid ID"""
    try:
        # Remove @lid suffix
        number_part = participant_id.replace('@lid', '')
        
        # Check if it looks like a Gambian number (starts with reasonable digits)
        if len(number_part) >= 10:
            # Try different patterns that might be Gambian numbers
            if number_part.startswith('220'):
                return number_part
            elif number_part.startswith('2203') or number_part.startswith('2207'):
                return number_part
            # Sometimes the number is embedded in a longer string
            elif '220' in number_part:
                # Extract 220 + following digits
                import re
                match = re.search(r'220\d{7,8}', number_part)
                if match:
                    return match.group()
                    
    except Exception as e:
        frappe.log_error(f"Error extracting number from {participant_id}: {str(e)}")
    
    return None

@frappe.whitelist(allow_guest=True)
def get_group_participants_detailed(instance: str, group_id: str):
    """Get detailed participant info for a specific group"""
    try:
        # First get basic group info
        url = f"{base_url}/group/fetchAllGroups/{instance}?getParticipants=true"
        headers = {"apikey": api_token}
        
        response = requests.get(url, headers=headers)
        groups_data = response.json()
        
        # Find the specific group
        target_group = None
        for group in groups_data.get('message', []):
            if group['id'] == group_id:
                target_group = group
                break
        
        if not target_group:
            return {"error": "Group not found"}
        
        # Resolve participants
        resolved_participants = resolve_participants_contacts(instance, target_group['participants'])
        
        return {
            "group_info": {
                "id": target_group['id'],
                "subject": target_group.get('subject'),
                "size": target_group.get('size'),
                "creation": target_group.get('creation')
            },
            "participants": resolved_participants,
            "summary": {
                "total_participants": len(resolved_participants),
                "regular_users": len([p for p in resolved_participants if p['type'] == 'regular']),
                "business_linked": len([p for p in resolved_participants if p['type'] == 'business_linked']),
                "resolved_phones": len([p for p in resolved_participants if p['actual_phone']])
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_group_participants_detailed: {str(e)}")
        return {"error": str(e)}

# Utility function to batch process multiple groups
@frappe.whitelist(allow_guest=True)
def batch_resolve_contacts(instance: str, max_groups: int = 5):
    """Resolve contacts for multiple groups with rate limiting"""
    try:
        groups_data = get_groups(instance)
        
        if not groups_data or 'message' not in groups_data:
            return {"error": "No groups found"}
        
        processed_groups = []
        
        for i, group in enumerate(groups_data['message'][:max_groups]):
            frappe.publish_progress(
                percent=(i+1)/min(max_groups, len(groups_data['message']))*100,
                title=f"Processing group {i+1}/{min(max_groups, len(groups_data['message']))}"
            )
            
            if 'participants' in group:
                resolved_participants = resolve_participants_contacts(instance, group['participants'])
                
                processed_groups.append({
                    "group_id": group['id'],
                    "subject": group.get('subject'),
                    "participants": resolved_participants
                })
                
                # Rate limiting between groups
                time.sleep(1)
        
        return {
            "processed_groups": processed_groups,
            "total_processed": len(processed_groups)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in batch_resolve_contacts: {str(e)}")
        return {"error": str(e)}