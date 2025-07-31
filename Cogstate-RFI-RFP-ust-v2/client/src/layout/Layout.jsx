import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { House, LayoutDashboard, FileText, BookOpen, RefreshCw } from "lucide-react";

// Side menu items
const sideMenuItems = [
  { id: 'dashboard', icon: House, label: 'Dashboard', path: '/' },
  { id: 'grid', icon: LayoutDashboard, label: 'Grid View', path: '/grid' },
  { id: 'documents', icon: FileText, label: 'Documents', path: '/documents' },
  { id: 'knowledge', icon: BookOpen, label: 'Knowledge Base', path: '/knowledgebase' },
  { id: 'sync', icon: RefreshCw, label: 'Sync', path: '/sync' },
];

// Top sub-menu items
const topSubMenuItems = [
  { id: 'dashboard', label: 'Dashboard', path: '/' },
  { id: 'rfi-rfp', label: 'RFI/RFP Responses', path: '/rfi-rfp' },
  { id: 'knowledge-base', label: 'Knowledge Base', path: '/knowledgebase' },
];

export default function Layout() {
  const [activeMenuItem, setActiveMenuItem] = useState('dashboard');
  const [activeSubMenuItem, setActiveSubMenuItem] = useState('dashboard');
  const navigate = useNavigate();
  const location = useLocation();

  // Check if current route should hide the top sub-menu
  const shouldHideSubMenu = location.pathname.match(/^\/response\/[\w-]+$/);

  // Update active menu items based on current route
  useEffect(() => {
    const currentPath = location.pathname;
    
    // Find matching side menu item
    const matchingSideItem = sideMenuItems.find(item => item.path === currentPath);
    if (matchingSideItem) {
      setActiveMenuItem(matchingSideItem.id);
    }
    
    // Find matching sub menu item
    const matchingSubItem = topSubMenuItems.find(item => item.path === currentPath);
    if (matchingSubItem) {
      setActiveSubMenuItem(matchingSubItem.id);
    }
  }, [location.pathname]);

  const handleSideMenuClick = (item) => {
    setActiveMenuItem(item.id);
    navigate(item.path);
    
    // If the side menu item has a corresponding sub menu item, activate it
    const correspondingSubItem = topSubMenuItems.find(subItem => subItem.path === item.path);
    if (correspondingSubItem) {
      setActiveSubMenuItem(correspondingSubItem.id);
    }
  };

  const handleSubMenuClick = (item) => {
    setActiveSubMenuItem(item.id);
    navigate(item.path);
    
    // Update side menu to match the sub menu selection
    const correspondingSideItem = sideMenuItems.find(sideItem => sideItem.path === item.path);
    if (correspondingSideItem) {
      setActiveMenuItem(correspondingSideItem.id);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />

      <main className="flex flex-1 overflow-hidden">
        {/* Side Menu */}
        <aside className="w-16 bg-light-gray border-r border-gray-200 flex flex-col h-full">
          <nav className="flex-1">
            {sideMenuItems.map((item) => (
              <div key={item.id} className="my-1 mx-2">
                <button
                  onClick={() => handleSideMenuClick(item)}
                  className={`w-full p-3 rounded-md flex flex-col items-center transition-colors duration-200 hover:bg-blue-50 ${
                    activeMenuItem === item.id
                      ? 'bg-secondary text-white hover:bg-primary'
                      : 'text-primary hover:text-white hover:bg-secondary'
                  }`}
                  title={item.label}
                >
                  <item.icon size={16} strokeWidth={1.5} className="cursor-pointer" />
                </button>
              </div>
            ))}
          </nav>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Sub-menu - Hidden for /response/id routes */}
          {!shouldHideSubMenu && (
            <nav className="bg-slate-800 text-white">
              <div className="flex">
                {topSubMenuItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleSubMenuClick(item)}
                    className={`px-6 py-3 text-xs font-bold transition-colors border-t-4 duration-200 ${
                      activeSubMenuItem === item.id
                        ? 'bg-white border-secondary text-primary'
                        : 'border-primary text-white hover:bg-secondary hover:border-secondary'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </nav>
          )}
          <div className="flex-1 overflow-auto">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}