"""
PDF Content Preview Page for QuizGenius MVP
Displays extracted PDF content with quality indicators and validation feedback
"""

import streamlit as st
from typing import Dict, Any, Optional

from services.content_validation_service import ContentValidationService
from utils.session_manager import SessionManager


class PDFContentPreviewPage:
    """PDF Content Preview page for instructors"""
    
    def __init__(self):
        """Initialize PDF content preview page"""
        self.content_validator = ContentValidationService()
        self.session_manager = SessionManager()
        
    def render(self):
        """Render the PDF content preview page"""
        st.title("👀 PDF Content Preview")
        st.markdown("Review the extracted content and quality assessment before generating questions.")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.error("Please log in to view content preview.")
            return
            
        # Check if we have content to preview
        if not self._has_content_to_preview():
            st.warning("No content available for preview. Please upload a PDF first.")
            if st.button("📄 Upload PDF"):
                st.session_state['page'] = 'pdf_upload'
                st.rerun()
            return
            
        # Get content data
        extracted_text = st.session_state.get('extracted_text', '')
        validation_result = st.session_state.get('validation_result')
        document_data = st.session_state.get('current_document', {})
        
        # Render preview interface
        self._render_document_info(document_data)
        self._render_quality_assessment(validation_result)
        self._render_content_preview(extracted_text)
        self._render_action_buttons(document_data, validation_result)
        
    def _has_content_to_preview(self) -> bool:
        """Check if there's content available for preview"""
        return (
            'extracted_text' in st.session_state and 
            st.session_state['extracted_text'] and
            'validation_result' in st.session_state
        )
        
    def _render_document_info(self, document_data: Dict[str, Any]):
        """Render document information header"""
        if not document_data:
            return
            
        st.subheader("📄 Document Information")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("File Name", document_data.get('filename', 'Unknown'))
        with col2:
            st.metric("File Size", f"{document_data.get('file_size', 0) / 1024 / 1024:.1f} MB")
        with col3:
            st.metric("Word Count", document_data.get('word_count', 0))
        with col4:
            upload_time = document_data.get('upload_timestamp', '')[:19] if document_data.get('upload_timestamp') else 'Unknown'
            st.metric("Upload Time", upload_time)
            
    def _render_quality_assessment(self, validation_result):
        """Render content quality assessment"""
        if not validation_result:
            return
            
        st.subheader("🔍 Content Quality Assessment")
        
        # Quality score and suitability
        col1, col2, col3 = st.columns(3)
        with col1:
            score_color = self._get_score_color(validation_result.quality_score)
            st.metric(
                "Quality Score", 
                f"{validation_result.quality_score:.1f}/10",
                help="Overall content quality for question generation"
            )
        with col2:
            suitable_text = "✅ Suitable" if validation_result.is_suitable else "❌ Not Suitable"
            st.metric("Question Generation", suitable_text)
        with col3:
            content_type = validation_result.metadata['detailed_analysis']['content_type'].replace('_', ' ').title()
            st.metric("Content Type", content_type)
            
        # Detailed analysis
        self._render_detailed_analysis(validation_result.metadata['detailed_analysis'])
        
        # Issues and recommendations
        if validation_result.issues:
            st.subheader("⚠️ Content Issues")
            for issue in validation_result.issues:
                st.warning(f"• {issue}")
                
        if validation_result.recommendations:
            st.subheader("💡 Recommendations")
            for rec in validation_result.recommendations:
                st.info(f"• {rec}")
                
    def _render_detailed_analysis(self, analysis):
        """Render detailed content analysis"""
        with st.expander("📊 Detailed Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Structure Scores:**")
                st.write(f"• Structure score: {analysis.get('structure_score', 0):.1f}/6")
                st.write(f"• Vocabulary complexity: {analysis.get('vocabulary_complexity', 0):.1f}/4")
                st.write(f"• Sentence complexity: {analysis.get('sentence_complexity', 0):.1f}/4")
                
                st.write("**Content Analysis:**")
                paragraph_structure = analysis.get('paragraph_structure', {})
                st.write(f"• Paragraphs: {paragraph_structure.get('count', 0)}")
                st.write(f"• Avg paragraph length: {paragraph_structure.get('average_length', 0):.1f} words")
                
            with col2:
                st.write("**Educational Indicators:**")
                st.write(f"• Educational keywords: {analysis.get('educational_keywords_count', 0)}")
                st.write(f"• Content type: {analysis.get('content_type', 'unknown').replace('_', ' ').title()}")
                
                topic_indicators = analysis.get('topic_indicators', [])
                if topic_indicators:
                    st.write("**Key Topics:**")
                    for topic in topic_indicators[:5]:  # Show first 5
                        st.write(f"• {topic}")
                        
    def _render_content_preview(self, extracted_text: str):
        """Render the extracted content preview"""
        st.subheader("📖 Extracted Content")
        
        if not extracted_text:
            st.warning("No text content was extracted from the PDF.")
            return
            
        # Content length info
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Characters", f"{char_count:,}")
        with col2:
            st.metric("Words", f"{word_count:,}")
        with col3:
            estimated_questions = max(1, word_count // 100)  # Rough estimate
            st.metric("Est. Questions", estimated_questions)
            
        # Content display options
        display_option = st.radio(
            "Display Options:",
            ["Preview (first 1000 characters)", "Full Content", "Summary"],
            horizontal=True
        )
        
        if display_option == "Preview (first 1000 characters)":
            preview_text = extracted_text[:1000]
            if len(extracted_text) > 1000:
                preview_text += "..."
            st.text_area(
                "Content Preview",
                preview_text,
                height=300,
                disabled=True
            )
            if len(extracted_text) > 1000:
                st.info(f"Showing first 1000 characters of {len(extracted_text)} total characters.")
                
        elif display_option == "Full Content":
            st.text_area(
                "Full Content",
                extracted_text,
                height=400,
                disabled=True
            )
            
        elif display_option == "Summary":
            self._render_content_summary(extracted_text)
            
    def _render_content_summary(self, extracted_text: str):
        """Render a summary of the content"""
        # Simple content analysis
        lines = extracted_text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # Find potential headings (lines that are shorter and might be titles)
        potential_headings = []
        for line in non_empty_lines[:20]:  # Check first 20 lines
            if len(line) < 100 and len(line.split()) < 15:
                potential_headings.append(line)
                
        st.write("**Content Structure:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"• Total lines: {len(lines)}")
            st.write(f"• Non-empty lines: {len(non_empty_lines)}")
            st.write(f"• Potential headings: {len(potential_headings)}")
            
        with col2:
            # Show first few potential headings
            if potential_headings:
                st.write("**Potential Headings:**")
                for heading in potential_headings[:5]:
                    st.write(f"• {heading}")
                    
        # Show first few paragraphs
        paragraphs = [p.strip() for p in extracted_text.split('\n\n') if p.strip()]
        if paragraphs:
            st.write("**First Few Paragraphs:**")
            for i, para in enumerate(paragraphs[:3]):
                if len(para) > 200:
                    para = para[:200] + "..."
                st.write(f"**Paragraph {i+1}:** {para}")
                
    def _render_action_buttons(self, document_data: Dict[str, Any], validation_result):
        """Render action buttons"""
        st.subheader("🚀 Next Steps")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Upload New PDF", use_container_width=True):
                st.session_state['page'] = 'pdf_upload'
                st.rerun()
                
        with col2:
            if st.button("🔄 Re-analyze Content", use_container_width=True):
                self._reanalyze_content()
                
        with col3:
            if validation_result and validation_result.is_suitable:
                if st.button("🤖 Generate Questions", type="primary", use_container_width=True):
                    st.session_state['page'] = 'question_generation'
                    st.rerun()
            else:
                st.button("🤖 Generate Questions", disabled=True, use_container_width=True)
                st.caption("Content not suitable for question generation")
                
    def _reanalyze_content(self):
        """Re-analyze the content"""
        if 'extracted_text' not in st.session_state:
            st.error("No content to re-analyze")
            return
            
        with st.spinner("Re-analyzing content..."):
            try:
                extracted_text = st.session_state['extracted_text']
                validation_result = self.content_validator.validate_content(extracted_text)
                st.session_state['validation_result'] = validation_result
                
                # Update document data if available
                if 'current_document' in st.session_state:
                    st.session_state['current_document'].update({
                        'quality_score': validation_result.quality_score,
                        'is_suitable': validation_result.is_suitable,
                        'content_type': validation_result.metadata['detailed_analysis']['content_type']
                    })
                    
                st.success("Content re-analyzed successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error re-analyzing content: {str(e)}")
                
    def _get_score_color(self, score: float) -> str:
        """Get color based on quality score"""
        if score >= 7:
            return "green"
        elif score >= 5:
            return "orange"
        else:
            return "red"


def render_pdf_content_preview_page():
    """Render the PDF content preview page"""
    page = PDFContentPreviewPage()
    page.render()


if __name__ == "__main__":
    render_pdf_content_preview_page()