"""
Rnanubandhan Network Analysis Module

This module provides advanced network analysis capabilities for the Rnanubandhan system.
It includes functions for analyzing karmic debt networks, identifying relationship patterns,
and providing insights into karmic communities.
"""

from typing import Dict, List, Any, Optional
from database import rnanubandhan_col, users_col
from utils.rnanubandhan import rnanubandhan_manager
import networkx as nx
import json
from datetime import datetime, timezone

class RnanubandhanNetworkAnalyzer:
    """Analyzes Rnanubandhan networks to provide insights into karmic relationships"""
    
    def __init__(self):
        """Initialize the network analyzer"""
        pass
    
    def build_network_graph(self, user_ids: Optional[List[str]] = None) -> nx.DiGraph:
        """
        Build a directed graph representation of the Rnanubandhan network.
        
        Args:
            user_ids (list, optional): List of user IDs to filter the network
            
        Returns:
            nx.DiGraph: NetworkX directed graph of karmic relationships
        """
        # Create a directed graph
        G = nx.DiGraph()
        
        # Query relationships
        query = {}
        if user_ids:
            query = {
                "$or": [
                    {"debtor_id": {"$in": user_ids}},
                    {"receiver_id": {"$in": user_ids}}
                ]
            }
        
        relationships = rnanubandhan_col.find(query)
        
        # Add nodes and edges to the graph
        for rel in relationships:
            debtor = rel["debtor_id"]
            receiver = rel["receiver_id"]
            amount = rel["amount"]
            severity = rel["severity"]
            status = rel["status"]
            
            # Add nodes (users)
            if not G.has_node(debtor):
                G.add_node(debtor, type="user")
            if not G.has_node(receiver):
                G.add_node(receiver, type="user")
            
            # Add edge (karmic debt)
            G.add_edge(
                debtor, receiver,
                amount=amount,
                severity=severity,
                status=status,
                relationship_id=str(rel["_id"]),
                created_at=rel["created_at"]
            )
        
        return G
    
    def get_network_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate network metrics for a specific user.
        
        Args:
            user_id (str): The user ID to analyze
            
        Returns:
            dict: Network metrics
        """
        # Build subgraph for the user's network
        G = self.build_network_graph([user_id])
        
        if not G.has_node(user_id):
            return {
                "user_id": user_id,
                "error": "User not found in network"
            }
        
        # Calculate metrics
        in_degree = G.in_degree(user_id)  # Credits (others owe to user)
        out_degree = G.out_degree(user_id)  # Debts (user owes to others)
        
        # Get neighbors
        creditors = list(G.predecessors(user_id))  # Who owes to user
        debtors = list(G.successors(user_id))  # To whom user owes
        
        # Calculate total amounts
        total_credit = sum(G[p][user_id]["amount"] for p in creditors if G.has_edge(p, user_id))
        total_debt = sum(G[user_id][s]["amount"] for s in debtors if G.has_edge(user_id, s))
        
        # Network centrality measures
        try:
            betweenness = nx.betweenness_centrality(G).get(user_id, 0)
            closeness = nx.closeness_centrality(G).get(user_id, 0)
        except:
            betweenness = 0
            closeness = 0
        
        return {
            "user_id": user_id,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "total_credit": total_credit,
            "total_debt": total_debt,
            "net_position": total_credit - total_debt,
            "creditors_count": len(creditors),
            "debtors_count": len(debtors),
            "creditors": creditors,
            "debtors": debtors,
            "betweenness_centrality": betweenness,
            "closeness_centrality": closeness,
            "relationship_diversity": len(set(creditors + debtors))
        }
    
    def find_karmic_communities(self, min_size: int = 3) -> List[Dict[str, Any]]:
        """
        Identify karmic communities (groups of users with dense relationships).
        
        Args:
            min_size (int): Minimum community size
            
        Returns:
            list: List of karmic communities
        """
        # Build the full network graph
        G = self.build_network_graph()
        
        if G.number_of_nodes() == 0:
            return []
        
        # Find communities using greedy modularity maximization
        try:
            communities = nx.community.greedy_modularity_communities(G.to_undirected())
        except:
            # Fallback if community detection fails
            return [{
                "community_id": "full_network",
                "members": list(G.nodes()),
                "size": G.number_of_nodes(),
                "total_relationships": G.number_of_edges()
            }]
        
        # Filter and format communities
        result = []
        for i, community in enumerate(communities):
            if len(community) >= min_size:
                # Calculate community metrics
                subgraph = G.subgraph(community)
                total_debt = sum(data["amount"] for u, v, data in subgraph.edges(data=True))
                
                result.append({
                    "community_id": f"community_{i}",
                    "members": list(community),
                    "size": len(community),
                    "total_relationships": subgraph.number_of_edges(),
                    "total_karmic_debt": total_debt,
                    "density": nx.density(subgraph),
                    "avg_clustering": nx.average_clustering(subgraph.to_undirected()) if len(community) > 1 else 0
                })
        
        return result
    
    def get_relationship_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze relationship patterns for a user.
        
        Args:
            user_id (str): The user ID to analyze
            
        Returns:
            dict: Relationship patterns
        """
        # Get user's relationships
        debts = rnanubandhan_manager.get_user_debts(user_id)
        credits = rnanubandhan_manager.get_user_credits(user_id)
        
        # Analyze by severity
        severity_counts = {"minor": 0, "medium": 0, "major": 0, "maha": 0}
        total_debt_amount = 0
        total_credit_amount = 0
        
        for debt in debts:
            severity = debt.get("severity", "minor")
            if severity in severity_counts:
                severity_counts[severity] += 1
            total_debt_amount += debt.get("amount", 0)
        
        for credit in credits:
            # For credits, we count from the debtor's perspective
            severity = credit.get("severity", "minor")
            if severity in severity_counts:
                severity_counts[severity] += 1
            total_credit_amount += credit.get("amount", 0)
        
        # Analyze by action type
        action_types = {}
        for debt in debts:
            action_type = debt.get("action_type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        for credit in credits:
            action_type = credit.get("action_type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        # Analyze by status
        status_counts = {"active": 0, "repaid": 0, "transferred": 0}
        for debt in debts:
            status = debt.get("status", "active")
            if status in status_counts:
                status_counts[status] += 1
        
        for credit in credits:
            status = credit.get("status", "active")
            if status in status_counts:
                status_counts[status] += 1
        
        return {
            "user_id": user_id,
            "severity_distribution": severity_counts,
            "action_type_distribution": action_types,
            "status_distribution": status_counts,
            "total_debt": total_debt_amount,
            "total_credit": total_credit_amount,
            "net_position": total_credit_amount - total_debt_amount,
            "debt_to_credit_ratio": total_debt_amount / max(total_credit_amount, 1),
            "relationship_count": len(debts) + len(credits)
        }
    
    def get_network_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a user's Rnanubandhan network.
        
        Args:
            user_id (str): The user ID to analyze
            
        Returns:
            dict: Comprehensive network summary
        """
        # Get basic network metrics
        metrics = self.get_network_metrics(user_id)
        
        # Get relationship patterns
        patterns = self.get_relationship_patterns(user_id)
        
        # Get network visualization data (simplified)
        G = self.build_network_graph([user_id])
        nodes = []
        edges = []
        
        # Prepare nodes
        for node in G.nodes():
            node_data = G.nodes[node]
            nodes.append({
                "id": node,
                "label": node,
                "type": node_data.get("type", "user"),
                "size": 20 if node == user_id else 10
            })
        
        # Prepare edges
        for u, v, data in G.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "amount": data.get("amount", 0),
                "severity": data.get("severity", "minor"),
                "status": data.get("status", "active"),
                "arrows": "to"
            })
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "patterns": patterns,
            "visualization": {
                "nodes": nodes,
                "edges": edges
            },
            "recommendations": self._generate_network_recommendations(metrics, patterns)
        }
    
    def _generate_network_recommendations(self, metrics: Dict, patterns: Dict) -> List[Dict]:
        """Generate recommendations based on network analysis"""
        recommendations = []
        
        # Recommendation based on net position
        net_position = metrics.get("net_position", 0)
        if net_position < -50:
            recommendations.append({
                "type": "debt_reduction",
                "priority": "high",
                "action": "focus_on_repaying_debts",
                "reasoning": f"Significant negative karmic position ({net_position})",
                "expected_benefit": "Improved relationship balance"
            })
        elif net_position > 50:
            recommendations.append({
                "type": "karmic_leadership",
                "priority": "medium",
                "action": "mentor_others_in_karmic_balance",
                "reasoning": f"Strong positive karmic position ({net_position})",
                "expected_benefit": "Enhanced spiritual leadership"
            })
        
        # Recommendation based on relationship diversity
        diversity = metrics.get("relationship_diversity", 0)
        if diversity < 3:
            recommendations.append({
                "type": "network_expansion",
                "priority": "medium",
                "action": "engage_with_more_community_members",
                "reasoning": "Limited relationship diversity",
                "expected_benefit": "Broader karmic connections"
            })
        
        # Recommendation based on debt severity
        high_severity_debts = patterns["severity_distribution"].get("major", 0) + patterns["severity_distribution"].get("maha", 0)
        if high_severity_debts > 2:
            recommendations.append({
                "type": "urgent_atonement",
                "priority": "high",
                "action": "address_high_severity_karmic_debts",
                "reasoning": f"{high_severity_debts} major/maha severity debts",
                "expected_benefit": "Significant karmic debt reduction"
            })
        
        return recommendations
    
    def export_network_data(self, user_id: str, format: str = "json") -> str:
        """
        Export network data in specified format.
        
        Args:
            user_id (str): The user ID
            format (str): Export format (json, csv)
            
        Returns:
            str: Exported data
        """
        if format.lower() == "json":
            summary = self.get_network_summary(user_id)
            return json.dumps(summary, indent=2, default=str)
        else:
            # For other formats, return a simple string representation
            summary = self.get_network_summary(user_id)
            return str(summary)

# Global instance
network_analyzer = RnanubandhanNetworkAnalyzer()

# Convenience functions
def get_network_summary(user_id: str) -> Dict[str, Any]:
    """Get comprehensive network summary for a user"""
    return network_analyzer.get_network_summary(user_id)

def find_karmic_communities(min_size: int = 3) -> List[Dict[str, Any]]:
    """Find karmic communities in the network"""
    return network_analyzer.find_karmic_communities(min_size)

def get_network_metrics(user_id: str) -> Dict[str, Any]:
    """Get network metrics for a user"""
    return network_analyzer.get_network_metrics(user_id)