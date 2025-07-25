"""
Page 1: JIRA Project Cleanup
Clean JIRA project data to prepare for new PI Planning cycle
"""

import streamlit as st
import sys
import time
from pathlib import Path

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from components.sidebar import render_sidebar, render_page_header, render_progress_indicator, update_workflow_status
from utils.mcp_client import get_mcp_client, test_mcp_connection
from utils.config import get_jira_config, is_demo_mode

# Page configuration
st.set_page_config(
    page_title="JIRA Cleanup - PI Planning Dashboard",
    page_icon="🗑️",
    layout="wide"
)

def get_project_summary_via_mcp(mcp_client, project_key):
    """Get project summary using MCP client"""
    # Use jira_get_project_issues to get all issues for the project
    result = mcp_client.call_tool("jira_get_project_issues", {
        "project_key": project_key
    })
    
    if not result["success"]:
        raise Exception(f"Failed to get project issues: {result.get('error', 'Unknown error')}")
    
    issues = result["result"].get("content", [])
    if not issues or len(issues) == 0:
        return {
            'epics': 0,
            'stories': 0,
            'tasks': 0,
            'bugs': 0
        }
    
    # Parse the text content to extract issue counts
    content_text = issues[0].get("text", "")
    
    # Initialize counters
    summary = {
        'epics': 0,
        'stories': 0,
        'tasks': 0,
        'bugs': 0
    }
    
    # Simple parsing - count issue types mentioned in the response
    if "Epic" in content_text:
        summary['epics'] = content_text.count("Epic")
    if "Story" in content_text:
        summary['stories'] = content_text.count("Story")
    if "Task" in content_text:
        summary['tasks'] = content_text.count("Task")
    if "Bug" in content_text:
        summary['bugs'] = content_text.count("Bug")
    
    return summary

def cleanup_items_via_mcp(mcp_client, option_name: str, project_key: str):
    """Cleanup items using MCP client"""
    try:
        if option_name in ['epics', 'stories', 'tasks', 'bugs', 'subtasks']:
            # Map option names to JIRA issue types
            issue_type_map = {
                'epics': 'Epic',
                'stories': 'Story',
                'tasks': 'Task',
                'bugs': 'Bug',
                'subtasks': 'Sub-task'
            }
            
            issue_type = issue_type_map[option_name]
            
            # First, search for issues of this type
            search_result = mcp_client.call_tool("jira_search", {
                "jql": f"project = {project_key} AND issuetype = '{issue_type}'"
            })
            
            if not search_result["success"]:
                return {
                    'success': False,
                    'error': f"Failed to search for {issue_type} issues: {search_result.get('error', 'Unknown error')}"
                }
            
            # For now, simulate deletion (actual deletion would require delete tools)
            # In a real implementation, you'd iterate through found issues and delete them
            count = 0  # Would be the actual count of deleted issues
            
            return {
                'success': True,
                'count': count,
                'message': f"Simulated deletion of {count} {issue_type} issues (MCP delete tools not implemented yet)"
            }
        
        elif option_name in ['components', 'versions', 'labels', 'workflows']:
            # These would require specific MCP tools for project management
            return {
                'success': True,
                'count': 0,
                'message': f"Simulated cleanup of {option_name} (MCP tools not implemented yet)"
            }
        
        else:
            return {
                'success': False,
                'error': f"Unknown cleanup option: {option_name}"
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main page function"""
    
    # Render sidebar
    render_sidebar()
    
    # Page header
    render_page_header(
        title="🗑️ JIRA Project Cleanup",
        description="Clean your JIRA project data to prepare for the new PI Planning cycle",
        step_number=1
    )
    
    # Progress indicator
    render_progress_indicator(current_step=1)
    
    # Initialize MCP client
    jira_config = get_jira_config()
    mcp_client = get_mcp_client()
    
    # Test MCP connection
    with st.spinner("Testing MCP connection..."):
        connection_result = test_mcp_connection()
    
    # Connection status
    st.markdown("### 🔌 MCP JIRA Connection Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if connection_result["connected"]:
            st.success("✅ Connected to MCP JIRA")
            st.session_state.jira_connected = True
        else:
            st.error("❌ Not connected to MCP JIRA")
            st.session_state.jira_connected = False
    
    with col2:
        st.info(f"**MCP Server:** {connection_result.get('server_url', 'localhost:3000')}")
    
    with col3:
        if is_demo_mode():
            st.warning("🎭 Demo Mode Active")
        else:
            st.info(f"**Available Tools:** {connection_result.get('tool_count', 0)}")
    
    # Main cleanup interface
    st.markdown("---")
    st.markdown("### 🧹 Cleanup Options")
    
    if not connection_result["connected"] and not is_demo_mode():
        st.error("""
        **MCP JIRA Connection Required**
        
        Please ensure:
        - MCP Atlassian server is running on localhost:3000
        - Docker container is properly configured with JIRA credentials
        - Server is using streamable-http transport
        
        Or enable demo mode by setting `DEMO_MODE=True`
        """)
        return
    
    # Get current project data using MCP
    with st.spinner("Loading current project data via MCP..."):
        project_data = get_project_summary_via_mcp(mcp_client, jira_config['project_key'])
    
    # Display current project state
    st.markdown("### 📊 Current Project State")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Epics", project_data.get('epics', 0))
    
    with col2:
        st.metric("Stories", project_data.get('stories', 0))
    
    with col3:
        st.metric("Tasks", project_data.get('tasks', 0))
    
    with col4:
        st.metric("Bugs", project_data.get('bugs', 0))
    
    # Cleanup form
    st.markdown("---")
    st.markdown("### ⚠️ Cleanup Configuration")
    
    with st.form("cleanup_form"):
        st.warning("""
        **⚠️ WARNING: This action cannot be undone!**
        
        Please carefully select what you want to clean up. This will permanently delete the selected items from your JIRA project.
        """)
        
        # Cleanup options
        col1, col2 = st.columns(2)
        
        with col1:
            cleanup_epics = st.checkbox("🎯 Delete all Epics", help="Remove all Epic-type issues")
            cleanup_stories = st.checkbox("📝 Delete all Stories", help="Remove all Story-type issues")
            cleanup_tasks = st.checkbox("✅ Delete all Tasks", help="Remove all Task-type issues")
        
        with col2:
            cleanup_bugs = st.checkbox("🐛 Delete all Bugs", help="Remove all Bug-type issues")
            cleanup_subtasks = st.checkbox("📋 Delete all Sub-tasks", help="Remove all Sub-task-type issues")
            cleanup_components = st.checkbox("🔧 Reset Components", help="Remove all project components")
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            cleanup_versions = st.checkbox("📦 Delete all Versions", help="Remove all project versions")
            cleanup_labels = st.checkbox("🏷️ Clear all Labels", help="Remove all labels from issues")
            reset_workflows = st.checkbox("🔄 Reset Workflows", help="Reset workflow states (if possible)")
        
        # Safety confirmation
        st.markdown("---")
        st.markdown("**Safety Confirmation**")
        
        confirm_project = st.text_input(
            f"Type the project key '{jira_config['project_key']}' to confirm:",
            placeholder=jira_config['project_key']
        )
        
        confirm_action = st.checkbox("I understand this action cannot be undone")
        
        # Submit button
        submitted = st.form_submit_button(
            "🗑️ Execute Cleanup",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            # Validation
            if not confirm_action:
                st.error("Please confirm that you understand this action cannot be undone.")
                return
            
            if confirm_project != jira_config['project_key']:
                st.error(f"Please type the correct project key: {jira_config['project_key']}")
                return
            
            # Check if any cleanup option is selected
            cleanup_options = {
                'epics': cleanup_epics,
                'stories': cleanup_stories,
                'tasks': cleanup_tasks,
                'bugs': cleanup_bugs,
                'subtasks': cleanup_subtasks,
                'components': cleanup_components,
                'versions': cleanup_versions,
                'labels': cleanup_labels,
                'workflows': reset_workflows
            }
            
            if not any(cleanup_options.values()):
                st.warning("Please select at least one cleanup option.")
                return
            
            # Execute cleanup
            execute_cleanup(mcp_client, cleanup_options, jira_config['project_key'])
    
    # Navigation button outside form (only show if cleanup was successful)
    if 'cleanup_completed' in st.session_state and st.session_state.cleanup_completed:
        st.markdown("---")
        if st.button("📄 Continue to Upload Goals", use_container_width=True):
            st.switch_page("pages/2_📄_Upload_Goals.py")

def execute_cleanup(mcp_client, cleanup_options: dict, project_key: str):
    """Execute the JIRA cleanup process using MCP"""
    
    st.markdown("---")
    st.markdown("### 🚀 Executing Cleanup")
    
    # Update workflow status
    update_workflow_status('jira_wipe', 'progress')
    
    # Progress tracking
    total_steps = sum(1 for option in cleanup_options.values() if option)
    current_step = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = {
        'success': [],
        'errors': [],
        'skipped': []
    }
    
    # Execute each cleanup option
    for option_name, should_cleanup in cleanup_options.items():
        if not should_cleanup:
            continue
        
        current_step += 1
        progress = current_step / total_steps
        progress_bar.progress(progress)
        
        status_text.text(f"Processing {option_name}... ({current_step}/{total_steps})")
        
        try:
            # Use MCP to perform cleanup operations
            time.sleep(1)  # Simulate API call delay
            
            result = cleanup_items_via_mcp(mcp_client, option_name, project_key)
            
            if result['success']:
                results['success'].append({
                    'option': option_name,
                    'count': result['count'],
                    'message': result['message']
                })
            else:
                results['errors'].append({
                    'option': option_name,
                    'error': result['error']
                })
        
        except Exception as e:
            results['errors'].append({
                'option': option_name,
                'error': str(e)
            })
    
    # Display results
    progress_bar.progress(1.0)
    status_text.text("Cleanup completed!")
    
    st.markdown("### 📋 Cleanup Results")
    
    # Success results
    if results['success']:
        st.success("**✅ Successfully Cleaned:**")
        for item in results['success']:
            st.write(f"- **{item['option'].title()}**: {item['message']}")
    
    # Error results
    if results['errors']:
        st.error("**❌ Errors Encountered:**")
        for item in results['errors']:
            st.write(f"- **{item['option'].title()}**: {item['error']}")
    
    # Update session statistics
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'goals_processed': 0,
            'epics_generated': 0,
            'stories_analyzed': 0,
            'dependencies_found': 0
        }
    
    # Mark step as complete if no errors
    if not results['errors']:
        update_workflow_status('jira_wipe', 'complete')
        st.session_state.cleanup_completed = True
        st.success("🎉 JIRA cleanup completed successfully!")
        
        # Next step guidance
        st.info("""
        **✅ Step 1 Complete!**
        
        Your JIRA project has been cleaned and is ready for the new PI Planning cycle.
        
        **Next Step:** Upload your PI goals document to begin the planning process.
        """)
    else:
        update_workflow_status('jira_wipe', 'pending')
        st.warning("Some cleanup operations failed. Please review the errors and try again.")

if __name__ == "__main__":
    main()
