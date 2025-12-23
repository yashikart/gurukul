import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSelector, useDispatch } from "react-redux";
import {
  LayoutDashboard,
  BookOpen,
  MessageSquare,
  Settings,
  FileText as FileTextIcon,
  Video,
  Cpu,
  FileDigit,
  UserCircle,
} from "lucide-react";
import MediaViewer from "./MediaViewer";
import {
  selectSelectedAvatar,
  selectFavorites,
  selectIsPinModeEnabled,
  selectIsChatOpen,
  setIsChatOpen,
} from "../store/avatarSlice";
import { selectIsAuthenticated } from "../store/authSlice";

export default function MobileBottomNavigation() {
  const { t } = useTranslation();
  const location = useLocation();
  const dispatch = useDispatch();
  
  // Redux state for avatar
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const selectedAvatar = useSelector(selectSelectedAvatar);
  const favorites = useSelector(selectFavorites);
  const isPinModeEnabled = useSelector(selectIsPinModeEnabled);
  const isChatOpen = useSelector(selectIsChatOpen);
  // Remove floating menu related code since we're using horizontal scroll
  // const [isMenuOpen, setIsMenuOpen] = useState(false);
  // const overlayRef = useRef(null);
  // const menuRef = useRef(null);
  // const fabRef = useRef(null);

  // All navigation items for horizontal scrolling
  const allNavItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
    { icon: MessageSquare, label: "Chatbot", href: "/chatbot" },
    { icon: BookOpen, label: "Subjects", href: "/subjects" },
    { icon: FileDigit, label: "Summarizer", href: "/learn" },
    { icon: FileTextIcon, label: "Test", href: "/test" },
    { icon: Video, label: "Lectures", href: "/lectures" },
    { icon: Cpu, label: "Agent Simulator", href: "/agent-simulator" },
    { icon: UserCircle, label: "Avatar", href: "/avatar-selection" },
    { icon: Settings, label: "Settings", href: "/settings" },
  ];

  // Remove floating menu functions since we're using horizontal scroll
  // const toggleMenu = () => {
  //   setIsMenuOpen(!isMenuOpen);
  // };

  // Remove floating menu animations since we're using horizontal scroll
  // useEffect(() => {
  //   // Animation logic removed
  // }, [isMenuOpen]);

  // Handle navigation item click
  const handleNavClick = () => {
    // Simple navigation, no menu to close
  };

  // Determine which avatar to render - prioritize selected avatar, then first favorite, then create fallback
  let avatarToRender = selectedAvatar;
  
  if (!avatarToRender && favorites.length > 0) {
    avatarToRender = favorites[0];
  }
  
  if (!avatarToRender) {
    // Create a temporary jupiter fallback avatar for rendering
    avatarToRender = {
      id: "temp-jupiter-fallback",
      name: "Brihaspati",
      isDefault: true,
      isPrimaryDefault: true,
      previewUrl: "/avatar/jupiter.glb",
      mediaType: "3d",
    };
  }
  
  // Get the display name for the current avatar
  const getAvatarDisplayName = () => {
    if (!avatarToRender) return "Brihaspati";
    
    try {
      // Try to get custom name from localStorage
      const customNames = JSON.parse(localStorage.getItem('avatar-custom-names') || '{}');
      if (customNames[avatarToRender.id]) {
        return customNames[avatarToRender.id];
      }
      
      // Use the avatar's name property if it exists
      if (avatarToRender.name) {
        return avatarToRender.name;
      }
      
      // For Jupiter avatar, use "Brihaspati"
      if (avatarToRender.id === 'jupiter-default' ||
          avatarToRender.id?.includes('jupiter') ||
          (avatarToRender.previewUrl && avatarToRender.previewUrl.includes('jupiter.glb'))) {
        return 'Brihaspati';
      }
      
      // Find the index in favorites to generate default name
      const avatarIndex = favorites.findIndex(fav => fav.id === avatarToRender.id);
      return avatarIndex >= 0 ? `Guru${avatarIndex + 1}` : "Brihaspati";
    } catch (error) {
      console.error('Error getting avatar display name:', error);
      return avatarToRender.name || "Brihaspati";
    }
  };
  
  // Handle guru name click to open chat
  const handleGuruNameClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only open chat if user is authenticated
    if (isAuthenticated) {
      dispatch(setIsChatOpen(!isChatOpen));
    }
  };
  
  // Determine avatar path
  let avatarPath = "/avatar/jupiter.glb"; // Default to jupiter
  
  if (avatarToRender.isCustomModel) {
    if (avatarToRender.previewUrl) {
      avatarPath = avatarToRender.previewUrl;
    }
  } else if (avatarToRender.isDefault || avatarToRender.previewUrl === "/avatar/jupiter.glb") {
    avatarPath = avatarToRender.previewUrl || "/avatar/jupiter.glb";
  } else if (avatarToRender.previewUrl && avatarToRender.previewUrl.endsWith(".glb")) {
    avatarPath = avatarToRender.previewUrl;
  } else if (avatarToRender.aiModel?.url && avatarToRender.aiModel.url.endsWith(".glb")) {
    avatarPath = avatarToRender.aiModel.url;
  }

  return (
    <>
      {/* Bottom Navigation Bar with Horizontal Scrolling */}
      <nav className="mobile-bottom-nav">
        <div className="mobile-nav-wrapper">
          {/* Branding Section with Guru Name and Avatar */}
          <div className="mobile-nav-branding">
            <span 
              className="mobile-nav-brand-text"
              onClick={handleGuruNameClick}
              style={{ cursor: isAuthenticated ? 'pointer' : 'default' }}
              title={isAuthenticated ? 'Click to chat with ' + getAvatarDisplayName() : getAvatarDisplayName()}
            >
              {getAvatarDisplayName()}
            </span>
            {isAuthenticated && avatarToRender && (
              <div className="mobile-nav-avatar">
                <MediaViewer
                  key={`mobile-nav-${avatarToRender?.id || "jupiter"}`}
                  mediaPath={avatarPath}
                  mediaType={avatarToRender?.mediaType}
                  isFloatingAvatar={false}
                  fallbackPath="/avatar/jupiter.glb"
                  enableControls={false}
                  autoRotate={avatarPath.includes('jupiter.glb')}
                  autoRotateSpeed={avatarPath.includes('jupiter.glb') ? 1.5 : 0.2}
                  showEnvironment={false}
                  fallbackMessage="Brihaspati"
                  className="w-full h-full"
                  rotation={[
                    0,
                    (180 * Math.PI) / 180,
                    0,
                  ]}
                  scale={0.8}
                  style="realistic"
                  enableInteraction={false}
                  enableAnimations={avatarPath.includes('jupiter.glb')}
                  cameraPosition={[0, 0, 1.5]}
                  fov={60}
                  lights={[
                    { type: "ambient", intensity: 0.8 },
                    { type: "directional", position: [2, 2, 2], intensity: 1.0 },
                  ]}
                />
              </div>
            )}
          </div>
          
          {/* Navigation Items Container */}
          <div className="mobile-nav-container-scroll">
            {allNavItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = item.href === location.pathname;
              
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={`mobile-nav-item-scroll ${isActive ? "active" : ""}`}
                  onClick={handleNavClick}
                >
                  <Icon size={20} />
                  <span className="mobile-nav-label">{t(item.label)}</span>
                  {isActive && <div className="mobile-nav-indicator" />}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>
    </>
  );
}