"""
Page 3: Generate Epics and Features
Generate Epics and Features from validated PI goals using AI agents
"""

import streamlit as st
import sys
import time
import pandas as pd
import io
from pathlib import Path
from typing import Dict, List, Any

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from components.sidebar import render_sidebar, render_page_header, render_progress_indicator, update_workflow_status
from agents.epic_generator import EpicGeneratorAgent
from utils.config import load_session_data, save_session_data, load_config
import openai

# Page configuration
st.set_page_config(
    page_title="Generate Epics - PI Planning Dashboard",
    page_icon="⚡",
    layout="wide"
)

def main():
    """Main page function"""
    
    # Render sidebar
    render_sidebar()
    
    # Page header
    render_page_header(
        title="⚡ Generate Epics & Features",
        description="Generate structured Epics and Features from your validated PI goals",
        step_number=3
    )
    
    # Progress indicator
    render_progress_indicator(current_step=3)
    
    # Check if previous step is complete
    workflow_status = st.session_state.get('workflow_status', {})
    if workflow_status.get('goals_upload') != 'complete':
        st.warning("""
        **⚠️ Previous Step Incomplete**
        
        Please complete Step 2 (Upload Goals) before proceeding with Epic generation.
        """)
        
        if st.button("📄 Go to Upload Goals", use_container_width=True):
            st.switch_page("pages/2_📄_Upload_Goals.py")
        return
    
    # Load processed goals from previous step
    processed_goals = load_session_data('processed_goals')
    
    if not processed_goals or not processed_goals.get('goals'):
        st.error("No processed goals found. Please complete Step 2 first.")
        if st.button("📄 Go to Upload Goals", use_container_width=True):
            st.switch_page("pages/2_📄_Upload_Goals.py")
        return
    
    # Display goals summary
    goals = processed_goals['goals']
    st.markdown("### 📋 Source Goals Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Goals", len(goals))
    with col2:
        high_priority = sum(1 for g in goals if g.get('priority') == 'High')
        st.metric("High Priority", high_priority)
    with col3:
        categories = set(g.get('category', 'Other') for g in goals)
        st.metric("Categories", len(categories))
    
    # Check if epics already generated
    generated_epics = load_session_data('generated_epics')
    
    if generated_epics:
        display_generated_epics(generated_epics)
    else:
        # Epic generation section
        st.markdown("---")
        st.markdown("### ⚡ Generate Epics & Features")
        
        st.info("""
        **AI Agent will:**
        - Break down each goal into actionable Epics
        - Generate Features for each Epic
        - Assign teams based on feature content
        - Estimate effort using story points
        - Create Excel export for review
        """)
        
        if st.button("🚀 Generate Epics & Features", use_container_width=True, type="primary"):
            generate_epics_and_features(goals)
    
    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back to Upload Goals", use_container_width=True):
            st.switch_page("pages/2_📄_Upload_Goals.py")
    
    with col2:
        # Enable next step if epics are generated
        next_disabled = not bool(generated_epics)
        if st.button("Continue to Review & Push →", use_container_width=True, disabled=next_disabled):
            if not next_disabled:
                st.switch_page("pages/4_📤_Review_Push.py")

def generate_epics_and_features(goals: List[Dict[str, Any]]):
    """Generate Epics and Features using AI agent"""
    
    st.markdown("---")
    st.markdown("### 🤖 AI Agent Processing")
    
    # Update workflow status
    update_workflow_status('epic_generation', 'progress')
    
    with st.spinner("Epic Generator Agent is analyzing your goals and creating Epics & Features..."):
        try:
            # Initialize Epic Generator Agent
            epic_agent = EpicGeneratorAgent()
            
            # Generate epics and features
            result = epic_agent.generate_epics_and_features(goals)
            
            # Save results
            save_session_data('generated_epics', result)
            
            # Update session statistics
            if 'session_stats' not in st.session_state:
                st.session_state.session_stats = {
                    'goals_processed': 0,
                    'epics_generated': 0,
                    'stories_analyzed': 0,
                    'dependencies_found': 0
                }
            
            st.session_state.session_stats['epics_generated'] = result['summary']['total_epics']
            
            # Mark step as complete
            update_workflow_status('epic_generation', 'complete')
            
            st.success("🎉 Epics and Features generated successfully!")
            
            # Display results
            display_generated_epics(result)
            
        except Exception as e:
            st.error(f"Error generating epics: {str(e)}")
            update_workflow_status('epic_generation', 'pending')

def display_generated_epics(result: Dict[str, Any]):
    """Display the generated epics and features"""
    
    st.markdown("---")
    st.markdown("### 📊 Generated Epics & Features")
    
    # Summary metrics
    summary = result.get('summary', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Epics", summary.get('total_epics', 0))
    with col2:
        st.metric("Features", summary.get('total_features', 0))
    with col3:
        st.metric("Story Points", summary.get('total_effort_points', 0))
    with col4:
        st.metric("Est. Weeks", summary.get('estimated_weeks', 0))
    
    # Team assignments
    team_assignments = result.get('team_assignments', {})
    if team_assignments:
        st.markdown("#### 👥 Team Assignments")
        
        team_cols = st.columns(len(team_assignments))
        for i, (team, features) in enumerate(team_assignments.items()):
            with team_cols[i]:
                st.markdown(f"**{team} Team**")
                st.write(f"{len(features)} features")
    
    # Epics details
    epics = result.get('epics', [])
    
    st.markdown("#### 🎯 Epic Details")
    
    for epic in epics:
        with st.expander(f"Epic: {epic.get('title', 'Untitled')}", expanded=False):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Description:**")
                st.write(epic.get('description', 'No description'))
                
                st.markdown("**Acceptance Criteria:**")
                criteria = epic.get('acceptance_criteria', [])
                for criterion in criteria:
                    st.write(f"• {criterion}")
            
            with col2:
                st.markdown("**Epic Info:**")
                st.write(f"**ID:** {epic.get('id', 'N/A')}")
                st.write(f"**Priority:** {epic.get('priority', 'Medium')}")
                st.write(f"**Category:** {epic.get('category', 'Business')}")
                st.write(f"**Features:** {epic.get('feature_count', 0)}")
                st.write(f"**Total Effort:** {epic.get('total_effort', 0)} points")
            
            # Features for this epic
            features = epic.get('features', [])
            if features:
                st.markdown("**Features:**")
                
                for feature in features:
                    with st.container():
                        st.markdown(f"**{feature.get('title', 'Untitled Feature')}**")
                        
                        feat_col1, feat_col2 = st.columns([3, 1])
                        
                        with feat_col1:
                            st.write(feature.get('description', 'No description'))
                            
                            # Acceptance criteria
                            feat_criteria = feature.get('acceptance_criteria', [])
                            if feat_criteria:
                                st.write("*Acceptance Criteria:*")
                                for criterion in feat_criteria:
                                    st.write(f"  • {criterion}")
                        
                        with feat_col2:
                            st.write(f"**Team:** {feature.get('assigned_team', 'TBD')}")
                            st.write(f"**Size:** {feature.get('effort_size', 'M')}")
                            st.write(f"**Points:** {feature.get('effort_points', 0)}")
                        
                        st.markdown("---")
    
    # Excel export section
    st.markdown("---")
    st.markdown("#### 📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export to Excel", use_container_width=True):
            excel_data = create_excel_export(result)
            st.download_button(
                label="💾 Download Excel File",
                data=excel_data,
                file_name="PI_Epics_and_Features.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        if st.button("🔄 Regenerate Epics", use_container_width=True):
            # Clear existing data
            if 'generated_epics' in st.session_state:
                del st.session_state['generated_epics']
            st.rerun()

def create_excel_export(result: Dict[str, Any]) -> bytes:
    """Create Excel export of epics and features"""
    
    # Create DataFrames for epics and features
    epics_data = []
    features_data = []
    
    for epic in result.get('epics', []):
        epics_data.append({
            'Epic ID': epic.get('id', ''),
            'Epic Title': epic.get('title', ''),
            'Description': epic.get('description', ''),
            'Priority': epic.get('priority', ''),
            'Category': epic.get('category', ''),
            'Status': epic.get('status', ''),
            'Feature Count': epic.get('feature_count', 0),
            'Total Effort': epic.get('total_effort', 0)
        })
        
        # Add features for this epic
        for feature in epic.get('features', []):
            features_data.append({
                'Epic ID': epic.get('id', ''),
                'Feature ID': feature.get('id', ''),
                'Feature Title': feature.get('title', ''),
                'Description': feature.get('description', ''),
                'Priority': feature.get('priority', ''),
                'Effort Size': feature.get('effort_size', ''),
                'Effort Points': feature.get('effort_points', 0),
                'Assigned Team': feature.get('assigned_team', ''),
                'Status': feature.get('status', ''),
                'Acceptance Criteria': '; '.join(feature.get('acceptance_criteria', []))
            })
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Epics sheet
        epics_df = pd.DataFrame(epics_data)
        epics_df.to_excel(writer, sheet_name='Epics', index=False)
        
        # Features sheet
        features_df = pd.DataFrame(features_data)
        features_df.to_excel(writer, sheet_name='Features', index=False)
        
        # Summary sheet
        summary_data = [{
            'Metric': 'Total Epics',
            'Value': result.get('summary', {}).get('total_epics', 0)
        }, {
            'Metric': 'Total Features',
            'Value': result.get('summary', {}).get('total_features', 0)
        }, {
            'Metric': 'Total Story Points',
            'Value': result.get('summary', {}).get('total_effort_points', 0)
        }, {
            'Metric': 'Estimated Weeks',
            'Value': result.get('summary', {}).get('estimated_weeks', 0)
        }]
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output.getvalue()

if __name__ == "__main__":
    main()
