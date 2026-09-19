"use client";

import React from "react";

interface PageHeaderProps {
  title: string;
  description: string;
  badge?: string;
  badgeColor?: "cyan" | "emerald" | "purple" | "blue";
  actions?: React.ReactNode;
}

export default function PageHeader({
  title,
  description,
  badge,
  badgeColor = "cyan",
  actions,
}: PageHeaderProps) {
  return (
    <div style={{
      display: "flex",
      alignItems: "flex-start",
      justifyContent: "space-between",
      gap: "20px",
      marginBottom: "28px",
      flexWrap: "wrap",
    }}>
      <div style={{ maxWidth: "800px" }}>
        {badge && (
          <div style={{ marginBottom: "10px" }}>
            <span className={`badge badge-${badgeColor}`}>
              <span className="badge-dot" />
              {badge}
            </span>
          </div>
        )}
        <h1 style={{
          fontSize: "2.1rem",
          fontWeight: 800,
          lineHeight: 1.2,
          letterSpacing: "-0.03em",
          color: "var(--text-primary)",
          marginBottom: "8px",
        }}>
          {title}
        </h1>
        <p style={{
          fontSize: "0.98rem",
          color: "var(--text-secondary)",
          lineHeight: 1.6,
        }}>
          {description}
        </p>
      </div>

      {actions && (
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "6px" }}>
          {actions}
        </div>
      )}
    </div>
  );
}
