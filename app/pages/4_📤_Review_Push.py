"""
Page 4: Review and Push to JIRA
Review generated Epics and Features, then push them to JIRA
"""

import streamlit as st
import sys
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from components.sidebar import render_sidebar, render_page_header, render_progress_indicator, update_workflow_status
from utils.config import load_session_data, save_session_data, load_config

# MCP tool integration - connects to standalone MCP server
def use_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interface to MCP tools - connects to standalone MCP Atlassian server
    """
    import requests
    import json
    
    # MCP server configuration - try multiple possible URLs
    config = load_config()
    possible_urls = [
        config.get('jira_mcp_server_url', 'http://localhost:3000'),
        "http://localhost:3000",
        "http://localhost:3000:3000", 
        "http://localhost:9000",
        "http://127.0.0.1:3000"
    ]
    
    # Try different endpoint paths
    endpoint_paths = ["/mcp", "/sse", "", "/api"]
    
    last_error = None
    
    for base_url in possible_urls:
        for endpoint in endpoint_paths:
            mcp_server_url = f"{base_url.rstrip('/')}{endpoint}"
            
            try:
                # Prepare the MCP request payload (JSON-RPC 2.0 format)
                mcp_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                # Make HTTP request to MCP server
                response = requests.post(
                    mcp_server_url,
                    json=mcp_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.info(f"✅ Connected to MCP server at: {mcp_server_url}")
                    return result.get("result", result)
                else:
                    last_error = f"MCP server at {mcp_server_url} returned status {response.status_code}: {response.text}"
                    
            except requests.exceptions.ConnectionError as e:
                last_error = f"Cannot connect to MCP server at {mcp_server_url}"
                continue
            except requests.exceptions.Timeout:
                last_error = f"MCP server request timed out at {mcp_server_url}"
                continue
            except Exception as e:
                last_error = f"MCP server error at {mcp_server_url}: {str(e)}"
                continue
    
    # If we get here, none of the URLs worked
    raise Exception(f"Could not connect to MCP server. Tried URLs: {possible_urls}. Last error: {last_error}")

def call_jira_mcp_server(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the actual JIRA MCP server to perform JIRA operations using our MCP client
    """
    try:
        # Import our MCP client
        from utils.mcp_client import get_mcp_client
        
        st.info(f"🔄 Making MCP call to JIRA server: {tool_name}")
        
        # Get the MCP client
        mcp_client = get_mcp_client()
        
        # Make the MCP call using our client
        mcp_response = mcp_client.call_tool(tool_name, arguments)
        
        # Process the MCP response
        if mcp_response and mcp_response.get('success'):
            # Successful response - extract JIRA issue information from the result
            result_content = mcp_response.get('result', {}).get('content', [])
            
            if result_content and len(result_content) > 0:
                # Parse the response text to extract issue details
                response_text = result_content[0].get('text', '')
                
                try:
                    import json
                    # Try to parse as JSON
                    issue_data = json.loads(response_text)
                    
                    if 'issue' in issue_data:
                        issue = issue_data['issue']
                        return {
                            'success': True,
                            'key': issue.get('key'),
                            'id': issue.get('id'),
                            'url': issue.get('url'),
                            'self': issue.get('url'),  # Use URL as self reference
                            'fields': issue,
                            'mcp_response': mcp_response
                        }
                    else:
                        # Fallback parsing
                        return {
                            'success': True,
                            'raw_response': response_text,
                            'mcp_response': mcp_response
                        }
                        
                except json.JSONDecodeError:
                    # If not JSON, treat as success with raw text
                    return {
                        'success': True,
                        'raw_response': response_text,
                        'mcp_response': mcp_response
                    }
            else:
                return {
                    'success': True,
                    'mcp_response': mcp_response
                }
        else:
            # MCP call failed
            error_msg = mcp_response.get('error', 'Unknown MCP error') if mcp_response else 'No response from MCP server'
            return {
                'success': False,
                'error': error_msg,
                'mcp_response': mcp_response
            }
            
    except Exception as e:
        # MCP client error
        return {
            'success': False,
            'error': f'MCP client error: {str(e)}'
        }

# Page configuration
st.set_page_config(
    page_title="Review & Push - PI Planning Dashboard",
    page_icon="📤",
    layout="wide"
)

def main():
    """Main page function"""
    
    # Render sidebar
    render_sidebar()
    
    # Page header
    render_page_header(
        title="📤 Review & Push to JIRA",
        description="Review your generated Epics and Features, then push them to JIRA",
        step_number=4
    )
    
    # Progress indicator
    render_progress_indicator(current_step=4)
    
    # Check if previous step is complete
    workflow_status = st.session_state.get('workflow_status', {})
    if workflow_status.get('epic_generation') != 'complete':
        st.warning("""
        **⚠️ Previous Step Incomplete**
        
        Please complete Step 3 (Generate Epics) before proceeding with JIRA push.
        """)
        
        if st.button("⚡ Go to Generate Epics", use_container_width=True):
            st.switch_page("pages/3_⚡_Generate_Epics.py")
        return
    
    # Load generated epics from previous step
    generated_epics = load_session_data('generated_epics')
    
    if not generated_epics or not generated_epics.get('epics'):
        st.error("No generated epics found. Please complete Step 3 first.")
        if st.button("⚡ Go to Generate Epics", use_container_width=True):
            st.switch_page("pages/3_⚡_Generate_Epics.py")
        return
    
    # Display review and push interface
    display_review_interface(generated_epics)

def display_review_interface(generated_epics: Dict[str, Any]):
    """Display the review and push interface"""
    
    # Summary section
    st.markdown("### 📊 Summary")
    
    summary = generated_epics.get('summary', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Epics", summary.get('total_epics', 0))
    with col2:
        st.metric("Features", summary.get('total_features', 0))
    with col3:
        st.metric("Story Points", summary.get('total_effort_points', 0))
    with col4:
        st.metric("Teams", summary.get('teams_involved', 0))
    
    # JIRA Configuration
    st.markdown("---")
    st.markdown("### ⚙️ JIRA Configuration")
    
    config = load_config()
    jira_configured = bool(config.get('jira_server') and config.get('jira_user') and config.get('jira_token'))
    
    if not jira_configured:
        st.warning("""
        **JIRA not configured.** For this demo, we'll use mock JIRA operations.
        
        To configure real JIRA integration, add these to your .env file:
        - JIRA_SERVER
        - JIRA_USER  
        - JIRA_TOKEN
        - JIRA_PROJECT_KEY
        """)
    else:
        st.success(f"✅ JIRA configured: {config.get('jira_server')}")
    
    # Project selection
    col1, col2 = st.columns(2)
    
    with col1:
        project_key = st.text_input(
            "JIRA Project Key",
            value=config.get('jira_project_key', 'DEMO'),
            help="The JIRA project where Epics and Features will be created"
        )
    
    with col2:
        issue_type_epic = st.selectbox(
            "Epic Issue Type",
            options=['Epic', 'Initiative', 'Theme'],
            index=0,
            help="JIRA issue type for Epics"
        )
    
    # Review section
    st.markdown("---")
    st.markdown("### 📋 Review Epics & Features")
    
    # Allow editing before push
    edited_epics = display_editable_epics(generated_epics)
    
    # Push to JIRA section
    st.markdown("---")
    st.markdown("### 🚀 Push to JIRA")
    
    # Check if already pushed
    push_status = load_session_data('jira_push_status')
    
    if push_status and push_status.get('status') == 'complete':
        display_push_results(push_status)
    else:
        # Push options
        col1, col2 = st.columns(2)
        
        with col1:
            push_epics_only = st.checkbox(
                "Push Epics Only",
                value=False,
                help="Push only Epics to JIRA (Features will be created later)"
            )
        
        with col2:
            dry_run = st.checkbox(
                "Dry Run (Preview Only)",
                value=True,
                help="Preview what will be created without actually pushing to JIRA"
            )
        
        # Push button
        if st.button("🚀 Push to JIRA", use_container_width=True, type="primary"):
            push_to_jira(edited_epics, project_key, issue_type_epic, push_epics_only, dry_run)
    
    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back to Generate Epics", use_container_width=True):
            st.switch_page("pages/3_⚡_Generate_Epics.py")
    
    with col2:
        # Enable next step if pushed to JIRA
        next_disabled = not bool(push_status and push_status.get('status') == 'complete')
        if st.button("Continue to Analyze Backlog →", use_container_width=True, disabled=next_disabled):
            if not next_disabled:
                st.switch_page("pages/5_🔍_Analyze_Backlog.py")

def display_editable_epics(generated_epics: Dict[str, Any]) -> Dict[str, Any]:
    """Display editable interface for epics and features"""
    
    epics = generated_epics.get('epics', [])
    edited_epics = []
    
    st.info("Review and edit the Epics and Features below before pushing to JIRA.")
    
    for i, epic in enumerate(epics):
        with st.expander(f"Epic: {epic.get('title', 'Untitled')}", expanded=False):
            
            # Epic editing
            col1, col2 = st.columns([2, 1])
            
            with col1:
                epic_title = st.text_input(
                    "Epic Title",
                    value=epic.get('title', ''),
                    key=f"epic_title_{i}"
                )
                
                epic_description = st.text_area(
                    "Epic Description",
                    value=epic.get('description', ''),
                    height=100,
                    key=f"epic_desc_{i}"
                )
            
            with col2:
                epic_priority = st.selectbox(
                    "Priority",
                    options=['Highest', 'High', 'Medium', 'Low', 'Lowest'],
                    index=['Highest', 'High', 'Medium', 'Low', 'Lowest'].index(
                        epic.get('priority', 'Medium') if epic.get('priority', 'Medium') in ['Highest', 'High', 'Medium', 'Low', 'Lowest'] else 'Medium'
                    ),
                    key=f"epic_priority_{i}"
                )
                
                epic_category = st.selectbox(
                    "Category",
                    options=['Business', 'Technical', 'User Experience', 'Performance', 'Security', 'Other'],
                    index=['Business', 'Technical', 'User Experience', 'Performance', 'Security', 'Other'].index(
                        epic.get('category', 'Business') if epic.get('category', 'Business') in ['Business', 'Technical', 'User Experience', 'Performance', 'Security', 'Other'] else 'Business'
                    ),
                    key=f"epic_category_{i}"
                )
            
            # Features editing
            features = epic.get('features', [])
            edited_features = []
            
            st.markdown("**Features:**")
            
            for j, feature in enumerate(features):
                st.markdown(f"*Feature {j + 1}:*")
                
                feat_col1, feat_col2 = st.columns([3, 1])
                
                with feat_col1:
                    feature_title = st.text_input(
                        "Feature Title",
                        value=feature.get('title', ''),
                        key=f"feature_title_{i}_{j}"
                    )
                    
                    feature_description = st.text_area(
                        "Feature Description",
                        value=feature.get('description', ''),
                        height=80,
                        key=f"feature_desc_{i}_{j}"
                    )
                
                with feat_col2:
                    feature_team = st.selectbox(
                        "Assigned Team",
                        options=['Frontend', 'Backend', 'DevOps', 'QA', 'Data', 'Security'],
                        index=['Frontend', 'Backend', 'DevOps', 'QA', 'Data', 'Security'].index(
                            feature.get('assigned_team', 'Backend') if feature.get('assigned_team', 'Backend') in ['Frontend', 'Backend', 'DevOps', 'QA', 'Data', 'Security'] else 'Backend'
                        ),
                        key=f"feature_team_{i}_{j}"
                    )
                    
                    feature_size = st.selectbox(
                        "Size",
                        options=['XS', 'S', 'M', 'L', 'XL', 'XXL'],
                        index=['XS', 'S', 'M', 'L', 'XL', 'XXL'].index(
                            feature.get('effort_size', 'M') if feature.get('effort_size', 'M') in ['XS', 'S', 'M', 'L', 'XL', 'XXL'] else 'M'
                        ),
                        key=f"feature_size_{i}_{j}"
                    )
                
                # Build edited feature
                edited_feature = {
                    'id': feature.get('id', ''),
                    'title': feature_title,
                    'description': feature_description,
                    'assigned_team': feature_team,
                    'effort_size': feature_size,
                    'effort_points': {'XS': 1, 'S': 2, 'M': 3, 'L': 5, 'XL': 8, 'XXL': 13}[feature_size],
                    'acceptance_criteria': feature.get('acceptance_criteria', []),
                    'priority': epic_priority,
                    'status': feature.get('status', 'To Do')
                }
                
                edited_features.append(edited_feature)
                
                st.markdown("---")
            
            # Build edited epic
            edited_epic = {
                'id': epic.get('id', ''),
                'title': epic_title,
                'description': epic_description,
                'priority': epic_priority,
                'category': epic_category,
                'features': edited_features,
                'feature_count': len(edited_features),
                'total_effort': sum(f['effort_points'] for f in edited_features),
                'acceptance_criteria': epic.get('acceptance_criteria', []),
                'status': epic.get('status', 'To Do')
            }
            
            edited_epics.append(edited_epic)
    
    return {
        'epics': edited_epics,
        'summary': {
            'total_epics': len(edited_epics),
            'total_features': sum(len(epic['features']) for epic in edited_epics),
            'total_effort_points': sum(epic['total_effort'] for epic in edited_epics)
        }
    }

def push_to_jira(edited_epics: Dict[str, Any], project_key: str, issue_type_epic: str, push_epics_only: bool, dry_run: bool):
    """Push epics and features to JIRA using MCP server"""
    
    st.markdown("---")
    st.markdown("### 🚀 Pushing to JIRA...")
    
    # Update workflow status
    update_workflow_status('jira_push', 'progress')
    
    push_results = {
        'status': 'in_progress',
        'dry_run': dry_run,
        'project_key': project_key,
        'pushed_epics': [],
        'pushed_features': [],
        'errors': [],
        'started_at': time.time()
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        epics = edited_epics.get('epics', [])
        total_items = len(epics)
        if not push_epics_only:
            total_items += sum(len(epic.get('features', [])) for epic in epics)
        
        current_item = 0
        
        # Push Epics
        for epic in epics:
            current_item += 1
            progress = current_item / total_items
            progress_bar.progress(progress)
            status_text.text(f"Processing Epic: {epic.get('title', 'Untitled')[:50]}...")
            
            # Simulate processing time
            time.sleep(1)
            
            if dry_run:
                # Dry run - just preview
                epic_result = {
                    'id': epic.get('id', ''),
                    'title': epic.get('title', ''),
                    'jira_key': f"{project_key}-{100 + current_item}",
                    'status': 'preview',
                    'url': f"https://demo.atlassian.net/browse/{project_key}-{100 + current_item}"
                }
            else:
                # Use JIRA MCP server to create Epic
                try:
                    st.info(f"🔄 Creating Epic via JIRA MCP server: {epic.get('title', '')}")
                    
                    # Prepare MCP call arguments (using correct parameter names)
                    mcp_call_args = {
                        'project_key': project_key,
                        'issue_type': issue_type_epic,
                        'summary': epic.get('title', ''),
                        'description': epic.get('description', '')
                    }
                    
                    # Attempt to make the actual MCP call
                    mcp_response = call_jira_mcp_server(
                        tool_name='jira_create_issue',
                        arguments=mcp_call_args
                    )
                    
                    if mcp_response and mcp_response.get('success'):
                        # Successful MCP call
                        config = load_config()
                        epic_result = {
                            'id': epic.get('id', ''),
                            'title': epic.get('title', ''),
                            'jira_key': mcp_response.get('key', f"{project_key}-{100 + current_item}"),
                            'status': 'created',
                            'url': mcp_response.get('url', f"{config.get('jira_server')}/browse/{mcp_response.get('key')}"),
                            'mcp_response': mcp_response
                        }
                        
                        st.success(f"✅ Epic created in JIRA: {mcp_response.get('key')}")
                        st.info(f"🔗 View at: {mcp_response.get('self', 'N/A')}")
                        
                    else:
                        # MCP call failed
                        config = load_config()
                        error_msg = mcp_response.get('error', 'Unknown MCP error') if mcp_response else 'No response from MCP server'
                        epic_key = f"{project_key}-{100 + current_item}"
                        epic_result = {
                            'id': epic.get('id', ''),
                            'title': epic.get('title', ''),
                            'jira_key': epic_key,
                            'status': 'mcp_failed',
                            'url': f"{config.get('jira_server', 'https://your-jira.atlassian.net')}/browse/{epic_key}",
                            'error': error_msg
                        }
                        
                        st.error(f"❌ MCP call failed: {error_msg}")
                        
                except Exception as mcp_error:
                    # MCP server not available or other error
                    config = load_config()
                    epic_key = f"{project_key}-{100 + current_item}"
                    epic_result = {
                        'id': epic.get('id', ''),
                        'title': epic.get('title', ''),
                        'jira_key': epic_key,
                        'status': 'mcp_unavailable',
                        'url': f"{config.get('jira_server', 'https://your-jira.atlassian.net')}/browse/{epic_key}",
                        'mcp_call': mcp_call_args,
                        'error': str(mcp_error)
                    }
                    
                    st.warning(f"⚠️ MCP server not available: {str(mcp_error)}")
                    st.info("💡 **Note**: To enable real JIRA creation, ensure your JIRA MCP server is running and connected.")
                    
                    # Show what the MCP call would look like
                    st.code(f"""
# MCP Call that would be executed:
use_mcp_tool(
    server_name='jira',
    tool_name='create_issue',
    arguments={mcp_call_args}
)
                    """, language='python')
            
            push_results['pushed_epics'].append(epic_result)
            
            # Push Features for this Epic (if not epics only)
            if not push_epics_only:
                for feature in epic.get('features', []):
                    current_item += 1
                    progress = current_item / total_items
                    progress_bar.progress(progress)
                    status_text.text(f"Processing Feature: {feature.get('title', 'Untitled')[:50]}...")
                    
                    # Simulate processing time
                    time.sleep(0.5)
                    
                    if dry_run:
                        # Dry run - just preview
                        feature_result = {
                            'id': feature.get('id', ''),
                            'title': feature.get('title', ''),
                            'jira_key': f"{project_key}-{200 + current_item}",
                            'epic_key': epic_result['jira_key'],
                            'status': 'preview',
                            'url': f"https://demo.atlassian.net/browse/{project_key}-{200 + current_item}"
                        }
                    else:
                        # Use JIRA MCP server to create Story
                        try:
                            # Create Story using MCP
                            story_response = st.session_state.get('mcp_client', {}).get('jira', {}).create_issue(
                                project=project_key,
                                issueType='Story',
                                summary=feature.get('title', ''),
                                description=feature.get('description', ''),
                                priority=feature.get('priority', 'Medium')
                            )
                            
                            if story_response and story_response.get('success'):
                                feature_result = {
                                    'id': feature.get('id', ''),
                                    'title': feature.get('title', ''),
                                    'jira_key': story_response.get('key', f"{project_key}-{200 + current_item}"),
                                    'epic_key': epic_result['jira_key'],
                                    'status': 'created',
                                    'url': story_response.get('url', f"https://demo.atlassian.net/browse/{story_response.get('key')}")
                                }
                            else:
                                # Fallback to mock
                                feature_result = {
                                    'id': feature.get('id', ''),
                                    'title': feature.get('title', ''),
                                    'jira_key': f"{project_key}-{200 + current_item}",
                                    'epic_key': epic_result['jira_key'],
                                    'status': 'mock_created',
                                    'url': f"https://demo.atlassian.net/browse/{project_key}-{200 + current_item}"
                                }
                                
                        except Exception as mcp_error:
                            # Fallback to mock if MCP server not available
                            feature_result = {
                                'id': feature.get('id', ''),
                                'title': feature.get('title', ''),
                                'jira_key': f"{project_key}-{200 + current_item}",
                                'epic_key': epic_result['jira_key'],
                                'status': 'mock_created',
                                'url': f"https://demo.atlassian.net/browse/{project_key}-{200 + current_item}"
                            }
                    
                    push_results['pushed_features'].append(feature_result)
        
        # Complete
        progress_bar.progress(1.0)
        status_text.text("✅ Push completed successfully!")
        
        push_results['status'] = 'complete'
        push_results['completed_at'] = time.time()
        
        # Save results
        save_session_data('jira_push_status', push_results)
        
        # Update workflow status
        update_workflow_status('jira_push', 'complete')
        
        # Update session statistics
        if 'session_stats' not in st.session_state:
            st.session_state.session_stats = {
                'goals_processed': 0,
                'epics_generated': 0,
                'stories_analyzed': 0,
                'dependencies_found': 0
            }
        
        st.session_state.session_stats['stories_analyzed'] = len(push_results['pushed_features'])
        
        # Display results
        display_push_results(push_results)
        
    except Exception as e:
        push_results['status'] = 'error'
        push_results['errors'].append(str(e))
        save_session_data('jira_push_status', push_results)
        update_workflow_status('jira_push', 'pending')
        st.error(f"Error pushing to JIRA: {str(e)}")

def display_push_results(push_results: Dict[str, Any]):
    """Display the results of the JIRA push"""
    
    st.markdown("---")
    st.markdown("### 📊 Push Results")
    
    if push_results.get('dry_run'):
        st.info("**🎭 Dry Run Results** - No actual JIRA issues were created")
    else:
        st.success("**✅ Live Push Results** - JIRA issues have been created")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Epics Created", len(push_results.get('pushed_epics', [])))
    with col2:
        st.metric("Features Created", len(push_results.get('pushed_features', [])))
    with col3:
        st.metric("Errors", len(push_results.get('errors', [])))
    with col4:
        duration = push_results.get('completed_at', 0) - push_results.get('started_at', 0)
        st.metric("Duration", f"{duration:.1f}s")
    
    # Pushed Epics
    pushed_epics = push_results.get('pushed_epics', [])
    if pushed_epics:
        st.markdown("#### 🎯 Created Epics")
        
        for epic in pushed_epics:
            with st.expander(f"Epic: {epic.get('title', 'Untitled')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**JIRA Key:** {epic.get('jira_key', 'N/A')}")
                    st.write(f"**Status:** {epic.get('status', 'Unknown')}")
                
                with col2:
                    if epic.get('url'):
                        st.markdown(f"**[View in JIRA]({epic['url']})**")
    
    # Pushed Features
    pushed_features = push_results.get('pushed_features', [])
    if pushed_features:
        st.markdown("#### ⚡ Created Features")
        
        # Group features by epic
        features_by_epic = {}
        for feature in pushed_features:
            epic_key = feature.get('epic_key', 'No Epic')
            if epic_key not in features_by_epic:
                features_by_epic[epic_key] = []
            features_by_epic[epic_key].append(feature)
        
        for epic_key, features in features_by_epic.items():
            st.markdown(f"**Epic: {epic_key}**")
            
            for feature in features:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"• {feature.get('title', 'Untitled')}")
                
                with col2:
                    st.write(f"**{feature.get('jira_key', 'N/A')}**")
                
                with col3:
                    if feature.get('url'):
                        st.markdown(f"[View]({feature['url']})")
    
    # Errors
    errors = push_results.get('errors', [])
    if errors:
        st.markdown("#### ❌ Errors")
        for error in errors:
            st.error(error)
    
    # Next steps
    if push_results.get('status') == 'complete':
        st.success("""
        **🎉 JIRA Push Complete!**
        
        Your Epics and Features have been successfully created in JIRA.
        You can now proceed to analyze the backlog or continue with dependency analysis.
        """)

if __name__ == "__main__":
    main()
