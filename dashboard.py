import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
import io
import traceback
import numpy as np
from dotenv import load_dotenv
from db_utils import get_analytics_data, get_recent_queries, analyze_sentiment

# Page configuration
st.set_page_config(
    page_title="HeadphoneGeek Customer Engagement Dashboard",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Custom CSS
st.markdown("""
<style>
    .header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #26A69A;
        margin-top: 20px;
    }
    .footer {
        font-size: 0.8rem;
        color: #616161;
        text-align: center;
        margin-top: 30px;
    }
    .metric-card {
        background-color: #f5f5f5;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .positive {
        color: #26A69A;
    }
    .neutral {
        color: #42A5F5;
    }
    .negative {
        color: #EF5350;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("<h1 class='header'>HeadphoneGeek Customer Engagement Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Analyze customer sentiment and engagement across platforms</p>", unsafe_allow_html=True)
    
    # Sidebar filters
    st.sidebar.header("Filters")
    platform = st.sidebar.selectbox("Select Platform", ["All", "Discord", "Reddit"], index=0)
    date_range = st.sidebar.slider("Date Range (days)", min_value=1, max_value=90, value=30, step=1)
    if st.sidebar.button("Refresh Data"):
        st.rerun()
        
    # Add current date display
    st.sidebar.markdown("---")
    st.sidebar.write(f"Data as of: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Add sentiment score guide
    st.sidebar.markdown("---")
    st.sidebar.subheader("Sentiment Guide")
    st.sidebar.markdown("""
    - **ADORE Score**: 0-100 scale (50 = neutral)
    - **Compound Score**: -1 to +1 scale
        - > 0.05: Positive 
        - -0.05 to 0.05: Neutral
        - < -0.05: Negative
    """)
    
    # Load analytics data
    try:
        df_analytics = get_analytics_data(days=date_range) if platform == "All" else get_analytics_data(days=date_range, platform=platform.lower())
        if df_analytics is None or df_analytics.empty:
            st.warning("No analytics data available for the selected filters.")
            st.info("Please try a different date range or platform, or check the database connection.")
            return
    except Exception as e:
        st.error(f"Error loading analytics data: {str(e)}")
        st.info("Please check the database connection or try again later.")
        return
    
    # Create a two-column layout for metrics
    col1, col2 = st.columns(2)
    
    # ADORE Score Section
    with col1:
        st.markdown("<h2 class='sub-header'>ADORE Score</h2>", unsafe_allow_html=True)
        try:
            if not df_analytics.empty and 'date' in df_analytics.columns and 'adore_score' in df_analytics.columns:
                latest_date = df_analytics['date'].max()
                latest_data = df_analytics[df_analytics['date'] == latest_date]
                
                if not latest_data.empty and 'adore_score' in latest_data.columns:
                    latest_adore = latest_data['adore_score'].mean()
                    adore_score = latest_adore if not pd.isnull(latest_adore) else 50
                    st.metric("Current ADORE Score", f"{adore_score:.1f}")
                    
                    # Add interpretation
                    if adore_score >= 75:
                        st.success("Excellent customer sentiment - Users are very satisfied!")
                    elif adore_score >= 60:
                        st.info("Good customer sentiment - Users are generally satisfied")
                    elif adore_score >= 40:
                        st.warning("Neutral customer sentiment - Mixed reactions")
                    else:
                        st.error("Poor customer sentiment - Improvement needed")
                else:
                    st.warning("No ADORE score data available for the selected period.")
                    st.metric("Default ADORE Score", "50.0")
            else:
                st.warning("No ADORE score data available.")
                st.metric("Default ADORE Score", "50.0")
        except Exception as e:
            st.error(f"Error calculating ADORE score: {str(e)}")
            st.metric("Default ADORE Score", "50.0")
    
    # Sentiment Summary Section
    with col2:
        st.markdown("<h2 class='sub-header'>Sentiment Summary</h2>", unsafe_allow_html=True)
        try:
            if not df_analytics.empty and all(col in df_analytics.columns for col in ['positive_count', 'neutral_count', 'negative_count']):
                total_sentiments = df_analytics[['positive_count', 'neutral_count', 'negative_count']].sum()
                total = total_sentiments.sum()
                
                if total > 0:
                    positive_pct = (total_sentiments['positive_count'] / total) * 100
                    neutral_pct = (total_sentiments['neutral_count'] / total) * 100
                    negative_pct = (total_sentiments['negative_count'] / total) * 100
                    
                    st.markdown(f"""
                        <div class='metric-card' style='background-color: #000000; color: #FFFFFF;'>
                        <p><span class='positive'>Positive: {total_sentiments['positive_count']} ({positive_pct:.1f}%)</span></p>
                        <p><span class='neutral'>Neutral: {total_sentiments['neutral_count']} ({neutral_pct:.1f}%)</span></p>
                        <p><span class='negative'>Negative: {total_sentiments['negative_count']} ({negative_pct:.1f}%)</span></p>
                        <p>Total Queries: {total}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No sentiment data available for the selected period.")
            else:
                st.info("Insufficient data for sentiment summary.")
        except Exception as e:
            st.error(f"Error calculating sentiment summary: {str(e)}")
    
    # ADORE Trend
    st.markdown("<h2 class='sub-header'>ADORE Score Trend</h2>", unsafe_allow_html=True)
    try:
        if not df_analytics.empty and 'date' in df_analytics.columns and 'platform' in df_analytics.columns and 'adore_score' in df_analytics.columns:
            adore_trend = df_analytics.groupby(['date', 'platform'])['adore_score'].mean().reset_index()
            if not adore_trend.empty:
                fig = px.line(adore_trend, x='date', y='adore_score', color='platform', title='ADORE Score Over Time')
                fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Neutral")
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trend data available for the selected period.")
        else:
            st.info("Insufficient data for ADORE score trend visualization.")
    except Exception as e:
        st.error(f"Error generating ADORE trend: {str(e)}")
    
    # Sentiment Distribution
    st.markdown("<h2 class='sub-header'>Sentiment Distribution</h2>", unsafe_allow_html=True)
    try:
        if not df_analytics.empty and all(col in df_analytics.columns for col in ['positive_count', 'neutral_count', 'negative_count']):
            sentiment_counts = df_analytics[['positive_count', 'neutral_count', 'negative_count']].sum()
            if sentiment_counts.sum() > 0:
                fig = px.pie(
                    values=sentiment_counts, 
                    names=['Positive', 'Neutral', 'Negative'], 
                    title='Sentiment Distribution',
                    color_discrete_sequence=['#26A69A', '#BBDEFB', '#EF5350']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sentiment data available for the selected period.")
        else:
            st.info("Insufficient data for sentiment distribution visualization.")
    except Exception as e:
        st.error(f"Error generating sentiment distribution: {str(e)}")
    
    # Sentiment Trend
    st.markdown("<h2 class='sub-header'>Sentiment Trend</h2>", unsafe_allow_html=True)
    try:
        if not df_analytics.empty and 'date' in df_analytics.columns and all(col in df_analytics.columns for col in ['positive_count', 'neutral_count', 'negative_count']):
            sentiment_trend = df_analytics.groupby('date')[['positive_count', 'neutral_count', 'negative_count']].sum().reset_index()
            if not sentiment_trend.empty and sentiment_trend[['positive_count', 'neutral_count', 'negative_count']].sum().sum() > 0:
                sentiment_melted = pd.melt(sentiment_trend, id_vars=['date'], var_name='sentiment', value_name='count')
                sentiment_melted['sentiment'] = sentiment_melted['sentiment'].apply(lambda x: x.replace('_count', '').capitalize())
                fig = px.line(
                    sentiment_melted, 
                    x='date', 
                    y='count', 
                    color='sentiment', 
                    title='Sentiment Trend',
                    color_discrete_map={
                        'Positive': '#26A69A',
                        'Neutral': '#BBDEFB',
                        'Negative': '#EF5350'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sentiment trend data available for the selected period.")
        else:
            st.info("Insufficient data for sentiment trend visualization.")
    except Exception as e:
        st.error(f"Error generating sentiment trend: {str(e)}")
    
    # Query Volume Comparison
    st.markdown("<h2 class='sub-header'>Query Volume Comparison</h2>", unsafe_allow_html=True)
    try:
        if not df_analytics.empty and all(col in df_analytics.columns for col in ['date', 'platform', 'query_count']):
            platform_trend = df_analytics.groupby(['date', 'platform'])['query_count'].sum().reset_index()
            if not platform_trend.empty and platform_trend['query_count'].sum() > 0:
                fig = px.bar(platform_trend, x='date', y='query_count', color='platform', title='Query Volume by Platform')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No query volume data available for the selected period.")
        else:
            st.info("Insufficient data for query volume visualization.")
    except Exception as e:
        st.error(f"Error generating query volume comparison: {str(e)}")
    
    # Recent Queries Section
    st.markdown("<h2 class='sub-header'>Recent Queries</h2>", unsafe_allow_html=True)
    
    # Handle Discord and Reddit separately due to different column names
    # Discord tab
    st.subheader("Discord")
    try:
        discord_queries = get_recent_queries("discord", limit=5)
        if discord_queries is not None and not discord_queries.empty:
            # Get the column list to check what's available
            columns = discord_queries.columns.tolist()
            display_cols = []
            
            # Conditionally include columns if they exist
            if 'content' in columns:
                display_cols.append('content')
            if 'category' in columns:
                display_cols.append('category')
            if 'sentiment_label' in columns:
                display_cols.append('sentiment_label')
            if 'sentiment_score' in columns:
                display_cols.append('sentiment_score')
            if 'timestamp' in columns:
                display_cols.append('timestamp')
            
            # Display table if we have columns to show
            if display_cols:
                # Rename columns for display
                renamed_df = discord_queries[display_cols].rename(
                    columns={
                        'content': 'Message',
                        'category': 'Category', 
                        'sentiment_label': 'Sentiment',
                        'sentiment_score': 'Score',
                        'timestamp': 'Time'
                    }
                )
                st.table(renamed_df)
            else:
                st.info("No displayable columns found in Discord data.")
        else:
            st.info("No recent Discord queries found.")
    except Exception as e:
        st.error(f"Error displaying Discord data: {str(e)}")
    
    # Reddit tab
    st.subheader("Reddit")
    try:
        reddit_queries = get_recent_queries("reddit", limit=5)
        if reddit_queries is not None and not reddit_queries.empty:
            # Get the column list to check what's available
            columns = reddit_queries.columns.tolist()
            display_cols = []
            
            # Conditionally include columns if they exist
            if 'title' in columns:
                display_cols.append('title')  # Reddit uses 'title' instead of 'content'
            if 'category' in columns:
                display_cols.append('category')
            if 'sentiment_label' in columns:
                display_cols.append('sentiment_label')
            if 'sentiment_score' in columns:
                display_cols.append('sentiment_score')
            if 'timestamp' in columns:
                display_cols.append('timestamp')
            
            # Display table if we have columns to show
            if display_cols:
                # Rename columns for display
                renamed_df = reddit_queries[display_cols].rename(
                    columns={
                        'title': 'Post Title',
                        'category': 'Category', 
                        'sentiment_label': 'Sentiment',
                        'sentiment_score': 'Score',
                        'timestamp': 'Time'
                    }
                )
                st.table(renamed_df)
            else:
                st.info("No displayable columns found in Reddit data.")
        else:
            st.info("No recent Reddit queries found.")
    except Exception as e:
        st.error(f"Error displaying Reddit data: {str(e)}")
    
    # Real-time Sentiment Analysis
    st.markdown("<h2 class='sub-header'>Real-time Sentiment Analysis</h2>", unsafe_allow_html=True)
    user_text = st.text_area("Enter text to analyze")
    if st.button("Analyze"):
        if user_text:
            try:
                sentiment = analyze_sentiment(user_text)
                
                # Create columns for better layout
                col1, col2 = st.columns(2)
                
                # Display score with color
                score = sentiment['score']
                if score > 0.05:
                    col1.markdown(f"<h3 class='positive'>Positive ({score:.2f})</h3>", unsafe_allow_html=True)
                elif score < -0.05:
                    col1.markdown(f"<h3 class='negative'>Negative ({score:.2f})</h3>", unsafe_allow_html=True)
                else:
                    col1.markdown(f"<h3 class='neutral'>Neutral ({score:.2f})</h3>", unsafe_allow_html=True)
                
                # Display ADORE equivalent
                adore_score = ((score + 1) / 2) * 100
                col2.metric("ADORE Equivalent", f"{adore_score:.1f}")
                
                # Text highlighting based on sentiment
                st.markdown("### Analyzed Text:")
                st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px; border-radius: 5px;'>{user_text}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error analyzing text: {str(e)}")
        else:
            st.warning("Please enter some text to analyze.")
    
    # Footer
    st.markdown("<div class='footer'>© 2025 HeadphoneGeek - Customer Engagement Dashboard</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()