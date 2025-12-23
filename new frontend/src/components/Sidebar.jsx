import React, { useRef, useEffect, useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import gsap from "gsap";
import {
  LayoutDashboard,
  BookOpen,
  MessageSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  FileText as FileTextIcon,
  Video,
  Cpu,
  FileDigit,
  UserCircle,
} from "lucide-react";

export default function Sidebar({ collapsed = false, onToggle }) {
  const { t } = useTranslation();
  const location = useLocation();
  const sidebarRef = useRef(null);
  const menuItemsRef = useRef([]);
  const toggleButtonRef = useRef(null);
  const settingsRef = useRef(null);

  // Use useMemo to prevent menuItems from being recreated on every render
  const menuItems = useMemo(
    () => [
      { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
      { icon: BookOpen, label: "Subjects", href: "/subjects" },
      { icon: FileDigit, label: "Summarizer", href: "/learn" },
      { icon: MessageSquare, label: "Chatbot", href: "/chatbot" },
      { icon: FileTextIcon, label: "Test", href: "/test" },
      { icon: Video, label: "Lectures", href: "/lectures" },
      { icon: Cpu, label: "Agent Simulator", href: "/agent-simulator" },
      { icon: UserCircle, label: "Avatar", href: "/avatar-selection" },
    ],
    []
  );

  // Reset refs when items change
  useEffect(() => {
    menuItemsRef.current = menuItemsRef.current.slice(0, menuItems.length);
  }, [menuItems.length]);

  // Animation when component mounts and when collapsed state changes
  useEffect(() => {
    if (!sidebarRef.current) return;

    // Kill any existing animations on the sidebar
    gsap.killTweensOf(sidebarRef.current);

    // Always ensure the sidebar is visible first
    gsap.set(sidebarRef.current, { opacity: 1 });

    // Create a timeline for the transition
    const tl = gsap.timeline({ defaults: { ease: "power2.out" } });

    // Different animations based on collapsed state
    if (collapsed) {
      // Transitioning from left sidebar to top bar
      tl.fromTo(
        sidebarRef.current,
        {
          width: "100%",
          height: "auto",
          x: 0,
          y: -20,
          opacity: 0.7,
          borderRadius: "1rem",
        },
        {
          width: "100%",
          height: "auto",
          x: 0,
          y: 0,
          opacity: 1,
          borderRadius: "0 0 1rem 1rem",
          duration: 0.25,
        }
      );

      // Animate menu items to slide in from top
      menuItemsRef.current.forEach((item, index) => {
        if (!item) return;
        tl.fromTo(
          item,
          { y: -15, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.2, delay: index * 0.02 },
          "-=0.15"
        );
      });

      // Animate settings item
      if (settingsRef.current) {
        tl.fromTo(
          settingsRef.current,
          { y: -15, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.2 },
          "-=0.1"
        );
      }
    } else {
      // Transitioning from top bar to left sidebar
      tl.fromTo(
        sidebarRef.current,
        {
          width: "100%",
          height: "auto",
          x: -20,
          opacity: 0.7,
          borderRadius: "0 1rem 1rem 0",
        },
        {
          width: "100%",
          height: "auto",
          x: 0,
          opacity: 1,
          borderRadius: "1rem",
          duration: 0.25,
        }
      );

      // Animate menu items to slide in from left
      menuItemsRef.current.forEach((item, index) => {
        if (!item) return;
        tl.fromTo(
          item,
          { x: -15, opacity: 0 },
          { x: 0, opacity: 1, duration: 0.2, delay: index * 0.02 },
          "-=0.15"
        );
      });

      // Animate settings item
      if (settingsRef.current) {
        tl.fromTo(
          settingsRef.current,
          { x: -15, opacity: 0 },
          { x: 0, opacity: 1, duration: 0.2 },
          "-=0.1"
        );
      }
    }

    // Play the timeline
    tl.play();

    // Cleanup function
    return () => {
      tl.kill();
    };
  }, [collapsed]);

  // Border animation for active menu items
  useEffect(() => {
    // Don't clear the global timeline as it affects other animations
    // Instead, we'll be more specific about which animations to kill

    // Create a master timeline for all animations
    const masterTimeline = gsap.timeline();

    // Function to create border animation for an element
    const createBorderAnimation = (element, isActive) => {
      if (!element) return;

      // Kill any existing animations on this element's borders
      gsap.killTweensOf(element, {
        props: [
          "borderBottomColor",
          "borderLeftColor",
          "borderTopColor",
          "borderRightColor",
        ],
      });

      // First, reset all borders to transparent
      gsap.set(element, {
        borderColor: "transparent",
        borderWidth: "2px",
        borderStyle: "solid",
        boxSizing: "border-box",
      });

      // If the item is active, create and return the animation
      if (isActive) {
        const tl = gsap.timeline({ id: "borderAnimation" + Math.random() });

        // Create a smooth sequence animation
        tl.to(element, {
          borderBottomColor: "#FFA94D",
          duration: 0.15,
          ease: "power1.inOut",
        })
          .to(
            element,
            {
              borderLeftColor: "#FFA94D",
              duration: 0.15,
              ease: "power1.inOut",
            },
            "-=0.05"
          ) // Slight overlap for smoother transition
          .to(
            element,
            {
              borderTopColor: "#FFA94D",
              duration: 0.15,
              ease: "power1.inOut",
            },
            "-=0.05"
          )
          .to(
            element,
            {
              borderRightColor: "#FFA94D",
              duration: 0.15,
              ease: "power1.inOut",
            },
            "-=0.05"
          );

        return tl;
      }

      return null;
    };

    // Process all menu items
    menuItemsRef.current.forEach((item, index) => {
      if (!item) return;

      const href = menuItems[index]?.href;
      const isActive = href === location.pathname;

      // Create animation and add to master timeline
      const animation = createBorderAnimation(item, isActive);
      if (animation) {
        masterTimeline.add(animation, 0); // Add at position 0 to run in parallel
      }
    });

    // Process settings item
    if (settingsRef.current) {
      const isSettingsActive = location.pathname === "/settings";

      // Create animation and add to master timeline
      const animation = createBorderAnimation(
        settingsRef.current,
        isSettingsActive
      );
      if (animation) {
        masterTimeline.add(animation, 0); // Add at position 0 to run in parallel
      }
    }

    // Play the master timeline
    masterTimeline.play();

    // Store references to elements for cleanup
    const elements = [
      ...menuItemsRef.current.filter((item) => item),
      settingsRef.current,
    ].filter(Boolean);

    // Cleanup function
    return () => {
      // Kill the master timeline
      if (masterTimeline) {
        masterTimeline.kill();
      }

      // Kill any border animations on specific elements
      elements.forEach((element) => {
        gsap.killTweensOf(element, {
          props: [
            "borderBottomColor",
            "borderLeftColor",
            "borderTopColor",
            "borderRightColor",
          ],
        });
      });
    };
  }, [location.pathname, menuItems, collapsed]);

  // Handle hover animations - animate text and icon while keeping background hover effect
  const handleMouseEnter = (element) => {
    // Add background hover effect
    gsap.to(element, {
      backgroundColor: "rgba(255, 255, 255, 0.2)",
      duration: 0.15,
      ease: "power2.out",
    });

    if (collapsed) {
      // For the icon in collapsed mode
      const icon = element.querySelector("svg");
      if (icon) {
        gsap.to(icon, {
          scale: 1.2,
          duration: 0.15,
          ease: "power2.out",
        });
      }
    } else {
      // Find the text span inside the element in expanded mode
      const textElement = element.querySelector("span");
      if (textElement) {
        gsap.to(textElement, {
          x: 5,
          duration: 0.15,
          ease: "power2.out",
        });
      }

      // For the main icon in expanded mode
      const icon = element.querySelector("svg:first-child");
      if (icon) {
        gsap.to(icon, {
          x: 3,
          scale: 1.1,
          duration: 0.15,
          ease: "power2.out",
        });
      }
    }
  };

  const handleMouseLeave = (element) => {
    // Get the href attribute to check if this is the active page
    const href = element.getAttribute("href");
    const isActive = href && location.pathname === href;

    // Remove background hover effect (unless it's active)
    gsap.to(element, {
      backgroundColor: isActive
        ? "rgba(255, 255, 255, 0.2)"
        : "rgba(255, 255, 255, 0)",
      duration: 0.15,
      ease: "power2.out",
    });

    if (collapsed) {
      // For the icon in collapsed mode
      const icon = element.querySelector("svg");
      if (icon) {
        gsap.to(icon, {
          scale: 1,
          duration: 0.15,
          ease: "power2.out",
        });
      }
    } else {
      // Find the text span inside the element in expanded mode
      const textElement = element.querySelector("span");
      if (textElement) {
        gsap.to(textElement, {
          x: 0,
          duration: 0.15,
          ease: "power2.out",
        });
      }

      // For the main icon in expanded mode
      const icon = element.querySelector("svg:first-child");
      if (icon) {
        gsap.to(icon, {
          x: 0,
          scale: 1,
          duration: 0.15,
          ease: "power2.out",
        });
      }
    }
  };

  // Handle click animation - faster and smoother
  const handleClick = (element) => {
    gsap
      .timeline()
      .to(element, {
        scale: 0.97,
        duration: 0.07,
        ease: "power2.in",
      })
      .to(element, {
        scale: 1,
        duration: 0.1,
        ease: "power2.out",
      });
  };

  return (
    <aside
      ref={sidebarRef}
      className={`transition-all duration-300 ease-in-out ${
        collapsed ? "w-full mx-auto my-0 rounded-b-2xl sticky z-40" : "h-auto rounded-2xl"
      }`}
      style={{
        marginTop: collapsed ? 0 : "1.3rem",
        marginBottom: collapsed ? 0 : "0",
        background: "rgba(30, 30, 40, 0.25)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: "0px solid rgba(255, 255, 255, 0.18)",
        borderRight: !collapsed ? "1px solid rgba(255, 255, 255, 0.18)" : "0px",
        borderBottom: collapsed ? "1px solid rgba(255, 255, 255, 0.18)" : "0px",
        boxShadow: collapsed
          ? "0 4px 12px rgba(0, 0, 0, 0.15), 0 1px 4px rgba(255, 215, 0, 0.05) inset"
          : "0 8px 32px rgba(0, 0, 0, 0.1), 0 1px 8px rgba(255, 215, 0, 0.05) inset",
        display: "flex",
        flexDirection: collapsed ? "row" : "column",
        justifyContent: collapsed ? "flex-start" : "flex-start",
        width: collapsed ? "100%" : "100%",
        maxWidth: collapsed ? "100%" : "100%",
        height: collapsed ? "auto" : "auto",
        padding: collapsed ? "0.35rem 0.25rem" : "0",
        top: collapsed ? "var(--header-h)" : undefined,
      }}
    >
      {/* Sidebar Content */}
      <div
        className={`flex ${
          collapsed ? "flex-row items-center" : "flex-col"
        } w-full`}
      >
        {/* Logo Area */}
        <div
          className={`${
            collapsed ? "py-1 px-3" : "py-5 px-5"
          } flex items-center ${
            collapsed ? "justify-center" : "justify-between"
          }`}
        >
          {!collapsed && (
            <span
              className="text-lg font-semibold text-white"
              style={{ fontFamily: "Nunito, sans-serif" }}
            >
              Menu
            </span>
          )}
          {onToggle && (
            <button
              ref={toggleButtonRef}
              onClick={(e) => {
                // Create a quick animation for the toggle button
                const btn = e.currentTarget;

                // Immediate feedback
                gsap.to(btn, {
                  scale: 0.8,
                  duration: 0.05,
                  ease: "power2.in",
                  onComplete: () => {
                    // Toggle state immediately for responsiveness
                    onToggle();

                    // Then animate back with a slight bounce
                    gsap.to(btn, {
                      scale: 1,
                      duration: 0.1,
                      ease: "back.out(1.5)",
                    });
                  },
                });
              }}
              className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center ml-2"
              onMouseEnter={(e) => handleMouseEnter(e.currentTarget)}
              onMouseLeave={(e) => handleMouseLeave(e.currentTarget)}
            >
              {collapsed ? (
                <ChevronLeft size={16} className="text-white" />
              ) : (
                <ChevronRight size={16} className="text-white" />
              )}
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <nav className={`${collapsed ? "py-1 flex-grow" : "py-3"}`}>
          <ul
            className={`${
              collapsed
                ? "px-2 flex flex-row items-center justify-start space-x-2 overflow-x-auto snap-x snap-mandatory whitespace-nowrap"
                : "px-3 space-y-2"
            }`}
          >
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = item.href === location.pathname;
              return (
                <li key={item.label}>
                  <Link
                    ref={(el) => (menuItemsRef.current[index] = el)}
                    to={item.href}
                    className={`
                      flex items-center rounded-lg
                      ${collapsed ? "py-2 px-3 mr-1 snap-start shrink-0" : "py-3 pl-4 pr-4"}
                      text-white/90
                      ${isActive ? "active-menu-item font-medium" : ""}
                    `}
                    style={{
                      backgroundColor: isActive
                        ? "rgba(255, 255, 255, 0.2)"
                        : "transparent",
                      transition: "background-color 0.15s ease",
                      borderWidth: "2px",
                      borderStyle: "solid",
                      borderColor: "transparent",
                      boxSizing: "border-box",
                    }}
                    onMouseEnter={(e) => handleMouseEnter(e.currentTarget)}
                    onMouseLeave={(e) => handleMouseLeave(e.currentTarget)}
                    onClick={(e) => handleClick(e.currentTarget)}
                  >
                    <Icon className="w-6 h-6 md:w-5 md:h-5 flex-shrink-0" />
                    {!collapsed && (
                      <span className="ml-3 truncate">{t(item.label)}</span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Settings Link */}
        <nav
          className={`${collapsed ? "py-1" : "py-3 mt-auto"}`}
          style={{
            borderTop: collapsed
              ? "none"
              : "1px solid rgba(255, 255, 255, 0.18)",
            borderLeft: collapsed
              ? "1px solid rgba(255, 255, 255, 0.18)"
              : "none",
            marginTop: collapsed ? "0" : "8px",
            marginLeft: collapsed ? "8px" : "0",
            paddingTop: collapsed ? "0" : "8px",
            paddingLeft: collapsed ? "8px" : "0",
          }}
        >
          <ul
            className={`${
              collapsed
                ? "px-2 flex flex-row items-center justify-start space-x-2 overflow-x-auto snap-x snap-mandatory whitespace-nowrap"
                : "px-3 space-y-2"
            }`}
          >
            <li>
              <Link
                ref={settingsRef}
                to="/settings"
                className={`
                  flex items-center rounded-lg
                  ${collapsed ? "py-2 px-3 mr-1 snap-start shrink-0" : "py-3 pl-4 pr-4"}
                  text-white/90
                  ${
                    location.pathname === "/settings"
                      ? "active-menu-item font-medium"
                      : ""
                  }
                `}
                style={{
                  backgroundColor:
                    location.pathname === "/settings"
                      ? "rgba(255, 255, 255, 0.2)"
                      : "transparent",
                  transition: "background-color 0.15s ease",
                  borderWidth: "2px",
                  borderStyle: "solid",
                  borderColor: "transparent",
                  boxSizing: "border-box",
                }}
                onMouseEnter={(e) => handleMouseEnter(e.currentTarget)}
                onMouseLeave={(e) => handleMouseLeave(e.currentTarget)}
                onClick={(e) => handleClick(e.currentTarget)}
              >
                <Settings className="w-6 h-6 md:w-5 md:h-5 flex-shrink-0" />
                {!collapsed && (
                  <span className="ml-3 truncate">{t("Settings")}</span>
                )}
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}
