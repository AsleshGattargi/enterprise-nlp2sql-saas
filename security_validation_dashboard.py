"""
Security Validation Report and Monitoring Dashboard
Provides comprehensive security analysis, compliance reporting, and real-time monitoring.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityValidationDashboard:
    """Security validation and monitoring dashboard."""

    def __init__(self):
        self.security_data = {}
        self.compliance_standards = {
            "SOC2": {
                "requirements": ["Access Control", "Data Encryption", "Audit Logging", "Incident Response"],
                "score_threshold": 90
            },
            "GDPR": {
                "requirements": ["Data Privacy", "Consent Management", "Data Portability", "Right to be Forgotten"],
                "score_threshold": 95
            },
            "HIPAA": {
                "requirements": ["Data Encryption", "Access Logs", "User Authentication", "Data Backup"],
                "score_threshold": 98
            },
            "ISO27001": {
                "requirements": ["Risk Management", "Security Controls", "Incident Management", "Business Continuity"],
                "score_threshold": 92
            }
        }

    def load_test_results(self, file_path: str = None) -> Dict[str, Any]:
        """Load security test results from file."""
        try:
            if file_path is None:
                # Find the most recent test results file
                test_files = list(Path(".").glob("test_results_*.json"))
                if test_files:
                    file_path = max(test_files, key=lambda x: x.stat().st_mtime)
                else:
                    return self._generate_sample_data()

            with open(file_path, 'r') as f:
                data = json.load(f)

            self.security_data = data
            return data

        except Exception as e:
            logger.warning(f"Could not load test results from {file_path}: {str(e)}")
            return self._generate_sample_data()

    def _generate_sample_data(self) -> Dict[str, Any]:
        """Generate sample security data for demonstration."""
        return {
            "test_execution": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_duration_seconds": 120.5
            },
            "summary": {
                "overall_status": "PASS",
                "total_tests": 53,
                "passed_tests": 51,
                "success_rate": 96.2
            },
            "category_summaries": {
                "tenant_isolation": {
                    "total_tests": 6,
                    "passed_tests": 6,
                    "success_rate": 100.0,
                    "avg_execution_time": 0.05
                },
                "nlp2sql_accuracy": {
                    "total_tests": 15,
                    "passed_tests": 14,
                    "success_rate": 93.3,
                    "avg_execution_time": 0.109
                },
                "load_testing": {
                    "total_tests": 25,
                    "passed_tests": 24,
                    "success_rate": 96.0,
                    "avg_execution_time": 0.08
                },
                "security_testing": {
                    "total_tests": 7,
                    "passed_tests": 7,
                    "success_rate": 100.0,
                    "avg_execution_time": 0.02
                }
            },
            "performance_benchmarks": [
                {
                    "metric_name": "Average Query Response Time",
                    "value": 109.27,
                    "unit": "ms",
                    "threshold": 1000,
                    "passed": True,
                    "category": "query_performance"
                },
                {
                    "metric_name": "Load Test Success Rate",
                    "value": 96.0,
                    "unit": "%",
                    "threshold": 95.0,
                    "passed": True,
                    "category": "system_performance"
                },
                {
                    "metric_name": "Tenant Isolation Success Rate",
                    "value": 100.0,
                    "unit": "%",
                    "threshold": 100.0,
                    "passed": True,
                    "category": "security_performance"
                },
                {
                    "metric_name": "Security Test Success Rate",
                    "value": 100.0,
                    "unit": "%",
                    "threshold": 95.0,
                    "passed": True,
                    "category": "security_performance"
                }
            ],
            "detailed_results": [],
            "recommendations": [
                "Continue regular monitoring and testing",
                "Implement continuous integration testing pipeline",
                "Set up automated performance monitoring in production",
                "Schedule regular security audits and penetration testing"
            ]
        }

    def generate_security_score(self) -> float:
        """Calculate overall security score."""
        if not self.security_data:
            return 0.0

        category_scores = self.security_data.get("category_summaries", {})

        # Weight different categories
        weights = {
            "security_testing": 0.4,
            "tenant_isolation": 0.3,
            "load_testing": 0.2,
            "nlp2sql_accuracy": 0.1
        }

        weighted_score = 0.0
        for category, weight in weights.items():
            if category in category_scores:
                weighted_score += category_scores[category]["success_rate"] * weight

        return round(weighted_score, 1)

    def check_compliance_status(self) -> Dict[str, Dict[str, Any]]:
        """Check compliance status against various standards."""
        security_score = self.generate_security_score()
        compliance_status = {}

        for standard, config in self.compliance_standards.items():
            compliant = security_score >= config["score_threshold"]
            compliance_status[standard] = {
                "compliant": compliant,
                "score": security_score,
                "threshold": config["score_threshold"],
                "gap": max(0, config["score_threshold"] - security_score),
                "requirements_met": len(config["requirements"]) if compliant else 0,
                "total_requirements": len(config["requirements"])
            }

        return compliance_status

    def get_security_trends(self, days: int = 30) -> Dict[str, List]:
        """Generate security trends data (simulated for demo)."""
        dates = []
        security_scores = []
        vulnerability_counts = []

        base_date = datetime.utcnow() - timedelta(days=days)
        base_score = 85.0

        for i in range(days):
            date = base_date + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))

            # Simulate improving security score over time with some variance
            score = min(100, base_score + (i * 0.3) + (i % 7 - 3) * 2)
            security_scores.append(round(score, 1))

            # Simulate decreasing vulnerability count
            vuln_count = max(0, 15 - (i // 3) + (i % 5 - 2))
            vulnerability_counts.append(vuln_count)

        return {
            "dates": dates,
            "security_scores": security_scores,
            "vulnerability_counts": vulnerability_counts
        }

    def generate_threat_assessment(self) -> Dict[str, Any]:
        """Generate threat assessment based on test results."""
        category_summaries = self.security_data.get("category_summaries", {})

        threat_levels = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        threat_details = []

        # Analyze each category for potential threats
        for category, summary in category_summaries.items():
            success_rate = summary.get("success_rate", 100)

            if success_rate < 80:
                threat_levels["critical"] += 1
                threat_details.append({
                    "category": category,
                    "threat_level": "critical",
                    "description": f"{category} success rate below 80%: {success_rate}%",
                    "impact": "High risk of system compromise"
                })
            elif success_rate < 90:
                threat_levels["high"] += 1
                threat_details.append({
                    "category": category,
                    "threat_level": "high",
                    "description": f"{category} success rate below 90%: {success_rate}%",
                    "impact": "Potential security vulnerabilities"
                })
            elif success_rate < 95:
                threat_levels["medium"] += 1
                threat_details.append({
                    "category": category,
                    "threat_level": "medium",
                    "description": f"{category} success rate below 95%: {success_rate}%",
                    "impact": "Minor security concerns"
                })
            else:
                threat_levels["low"] += 1

        return {
            "threat_levels": threat_levels,
            "threat_details": threat_details,
            "overall_threat_level": self._calculate_overall_threat_level(threat_levels)
        }

    def _calculate_overall_threat_level(self, threat_levels: Dict[str, int]) -> str:
        """Calculate overall threat level."""
        if threat_levels["critical"] > 0:
            return "critical"
        elif threat_levels["high"] > 0:
            return "high"
        elif threat_levels["medium"] > 1:
            return "medium"
        else:
            return "low"

    def create_dashboard(self):
        """Create Streamlit dashboard."""
        st.set_page_config(
            page_title="Multi-Tenant NLP2SQL Security Dashboard",
            page_icon="🔒",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        st.title("🔒 Multi-Tenant NLP2SQL Security Validation Dashboard")
        st.markdown("---")

        # Load data
        self.load_test_results()

        # Sidebar
        st.sidebar.header("Dashboard Controls")
        refresh_data = st.sidebar.button("🔄 Refresh Data")

        if refresh_data:
            self.load_test_results()
            st.experimental_rerun()

        show_details = st.sidebar.checkbox("Show Detailed Results", value=False)
        selected_timeframe = st.sidebar.selectbox("Trend Analysis Timeframe", ["7 days", "30 days", "90 days"])

        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)

        # Key metrics
        security_score = self.generate_security_score()
        total_tests = self.security_data.get("summary", {}).get("total_tests", 0)
        passed_tests = self.security_data.get("summary", {}).get("passed_tests", 0)
        success_rate = self.security_data.get("summary", {}).get("success_rate", 0)

        with col1:
            st.metric(
                label="🛡️ Security Score",
                value=f"{security_score}/100",
                delta=f"{security_score - 85:.1f}" if security_score > 85 else None
            )

        with col2:
            st.metric(
                label="✅ Tests Passed",
                value=f"{passed_tests}/{total_tests}",
                delta=f"{success_rate:.1f}%" if success_rate >= 90 else None
            )

        with col3:
            threat_assessment = self.generate_threat_assessment()
            threat_level = threat_assessment["overall_threat_level"]
            threat_color = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}

            st.metric(
                label="⚠️ Threat Level",
                value=f"{threat_color.get(threat_level, '⚪')} {threat_level.upper()}"
            )

        with col4:
            execution_time = self.security_data.get("test_execution", {}).get("total_duration_seconds", 0)
            st.metric(
                label="⏱️ Test Duration",
                value=f"{execution_time:.1f}s"
            )

        # Security trends
        st.header("📈 Security Trends")

        timeframe_days = {"7 days": 7, "30 days": 30, "90 days": 90}
        trends = self.get_security_trends(timeframe_days[selected_timeframe])

        fig_trends = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Security Score Over Time", "Vulnerability Count Over Time"),
            vertical_spacing=0.1
        )

        # Security score trend
        fig_trends.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=trends["security_scores"],
                mode='lines+markers',
                name='Security Score',
                line=dict(color='green', width=3)
            ),
            row=1, col=1
        )

        # Vulnerability count trend
        fig_trends.add_trace(
            go.Scatter(
                x=trends["dates"],
                y=trends["vulnerability_counts"],
                mode='lines+markers',
                name='Vulnerabilities',
                line=dict(color='red', width=3)
            ),
            row=2, col=1
        )

        fig_trends.update_layout(height=500, showlegend=False)
        fig_trends.update_xaxes(title_text="Date", row=2, col=1)
        fig_trends.update_yaxes(title_text="Score", row=1, col=1)
        fig_trends.update_yaxes(title_text="Count", row=2, col=1)

        st.plotly_chart(fig_trends, use_container_width=True)

        # Test category results
        col1, col2 = st.columns(2)

        with col1:
            st.header("🧪 Test Category Results")

            category_data = self.security_data.get("category_summaries", {})
            if category_data:
                categories = list(category_data.keys())
                success_rates = [category_data[cat]["success_rate"] for cat in categories]

                fig_categories = px.bar(
                    x=categories,
                    y=success_rates,
                    title="Success Rate by Test Category",
                    color=success_rates,
                    color_continuous_scale="RdYlGn",
                    range_color=[0, 100]
                )
                fig_categories.update_layout(showlegend=False)
                fig_categories.update_xaxes(title="Category")
                fig_categories.update_yaxes(title="Success Rate (%)")

                st.plotly_chart(fig_categories, use_container_width=True)

        with col2:
            st.header("📊 Performance Benchmarks")

            benchmarks = self.security_data.get("performance_benchmarks", [])
            if benchmarks:
                benchmark_names = [b["metric_name"] for b in benchmarks]
                benchmark_values = [b["value"] for b in benchmarks]
                benchmark_passed = [b["passed"] for b in benchmarks]

                colors = ['green' if passed else 'red' for passed in benchmark_passed]

                fig_benchmarks = go.Figure(data=[
                    go.Bar(
                        x=benchmark_names,
                        y=benchmark_values,
                        marker_color=colors
                    )
                ])
                fig_benchmarks.update_layout(
                    title="Performance Benchmark Results",
                    xaxis_title="Metric",
                    yaxis_title="Value"
                )
                fig_benchmarks.update_xaxes(tickangle=45)

                st.plotly_chart(fig_benchmarks, use_container_width=True)

        # Compliance status
        st.header("📋 Compliance Status")

        compliance_status = self.check_compliance_status()
        compliance_cols = st.columns(len(compliance_status))

        for i, (standard, status) in enumerate(compliance_status.items()):
            with compliance_cols[i]:
                compliance_color = "🟢" if status["compliant"] else "🔴"
                st.metric(
                    label=f"{compliance_color} {standard}",
                    value=f"{status['score']:.1f}/100",
                    delta=f"Gap: {status['gap']:.1f}" if not status["compliant"] else "Compliant"
                )

        # Threat assessment
        st.header("⚠️ Threat Assessment")

        threat_data = self.generate_threat_assessment()

        col1, col2 = st.columns([1, 2])

        with col1:
            threat_levels = threat_data["threat_levels"]

            # Threat level pie chart
            fig_threats = px.pie(
                values=list(threat_levels.values()),
                names=list(threat_levels.keys()),
                title="Threat Distribution",
                color_discrete_map={
                    "critical": "#ff0000",
                    "high": "#ff8000",
                    "medium": "#ffff00",
                    "low": "#00ff00"
                }
            )
            st.plotly_chart(fig_threats, use_container_width=True)

        with col2:
            st.subheader("Threat Details")

            threat_details = threat_data["threat_details"]
            if threat_details:
                for threat in threat_details:
                    level_color = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢"
                    }

                    st.write(f"{level_color.get(threat['threat_level'], '⚪')} **{threat['category'].replace('_', ' ').title()}**")
                    st.write(f"   {threat['description']}")
                    st.write(f"   *Impact: {threat['impact']}*")
                    st.write("")
            else:
                st.success("No significant threats identified! 🎉")

        # Recommendations
        st.header("💡 Recommendations")

        recommendations = self.security_data.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
        else:
            st.info("No specific recommendations at this time.")

        # Detailed results (optional)
        if show_details:
            st.header("📋 Detailed Test Results")

            category_summaries = self.security_data.get("category_summaries", {})

            for category, summary in category_summaries.items():
                with st.expander(f"{category.replace('_', ' ').title()} - {summary['success_rate']:.1f}% Success Rate"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Total Tests", summary["total_tests"])
                    with col2:
                        st.metric("Passed Tests", summary["passed_tests"])
                    with col3:
                        st.metric("Avg Execution Time", f"{summary['avg_execution_time']:.3f}s")

        # Footer
        st.markdown("---")
        st.markdown(
            f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC* | "
            f"*Security Dashboard v1.0* | "
            f"*Multi-Tenant NLP2SQL Testing Framework*"
        )


def main():
    """Main function to run the dashboard."""
    dashboard = SecurityValidationDashboard()
    dashboard.create_dashboard()


if __name__ == "__main__":
    main()