import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./MyPage.css";

export default function MyPage() {
  const navigate = useNavigate();

  // --- 상태 관리 ---
  const [currentProfile, setCurrentProfile] = useState('나');
  const [profiles, setProfiles] = useState(['나', '딸']);
  const [isEditing, setIsEditing] = useState(false);
  const [showInput, setShowInput] = useState(false);
  const [newProfileName, setNewProfileName] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [tagInput, setTagInput] = useState({ type: "", value: "" });

  const [profileData, setProfileData] = useState({
    '나': {
      allergies: ["새우", "계란", "아몬드"],
      dislikes: ["고추", "브로콜리", "파프리카", "회", "고등어"],
      tools: ["밥솥", "전자레인지", "오븐", "에어프라이어", "찜기"]
    },
    '딸': {
      allergies: ["새우"], dislikes: ["고추"], tools: ["밥솥"]
    }
  });

  const TOOL_LIST = [
    { name: "밥솥", icon: "/rice-cooker.png" }, { name: "전자레인지", icon: "/cooked.png", size: "100%" },
    { name: "오븐", icon: "/oven.png", size: "65%" }, { name: "에어프라이어", icon: "/air-fryer.png" },
    { name: "찜기", icon: "/food-steamer.png" }, { name: "믹서기", icon: "/blender.png" },
    { name: "착즙기", icon: "/citrus-juicer.png" }, { name: "커피머신", icon: "/coffe-machine.png" },
    { name: "토스트기", icon: "/toast-appliance.png" }, { name: "와플메이커", icon: "/stovetop-waffle.png" },
  ];

  // --- 데이터 로드 & 자동 저장 ---
  useEffect(() => {
    const saved = localStorage.getItem("mypage_storage");
    if (saved) {
      const { profiles: sProfiles, profileData: sData } = JSON.parse(saved);
      setProfiles(sProfiles);
      setProfileData(sData);
    }
  }, []);

  // 데이터 변경될 때마다 로컬 스토리지에 자동 저장 (나갔다 들어와도 유지됨)
  useEffect(() => {
    const dataToSave = { profiles, profileData };
    localStorage.setItem("mypage_storage", JSON.stringify(dataToSave));
  }, [profiles, profileData]);

  const currentData = profileData[currentProfile] || { allergies: [], dislikes: [], tools: [] };

  // --- 프로필 관련 ---
  const handleAddProfile = () => {
    const name = newProfileName.trim();
    if (name && !profiles.includes(name)) {
      setProfiles([...profiles, name]);
      setProfileData({ ...profileData, [name]: { allergies: [], dislikes: [], tools: [] } });
      setCurrentProfile(name);
    }
    setNewProfileName("");
    setShowInput(false);
  };

  const confirmDelete = () => {
    const newProfiles = profiles.filter(p => p !== deleteTarget);
    setProfiles(newProfiles);
    setCurrentProfile(newProfiles[0] || "");
    setDeleteTarget(null);
  };

  // --- 태그 관련 ---
  const addTag = (type) => {
    const val = tagInput.value.trim();
    if (val && !currentData[type].includes(val)) {
      setProfileData({
        ...profileData,
        [currentProfile]: { ...currentData, [type]: [...currentData[type], val] }
      });
    }
    setTagInput({ type: "", value: "" });
  };

  const removeTag = (type, targetTag) => {
    if (!isEditing) return;
    setProfileData({
      ...profileData,
      [currentProfile]: { ...currentData, [type]: currentData[type].filter(t => t !== targetTag) }
    });
  };

  // --- 조리도구 토글 (수정 모드가 아닐 때도 작동) ---
  const toggleTool = (toolName) => {
    const currentTools = currentData.tools;
    const newTools = currentTools.includes(toolName)
      ? currentTools.filter(t => t !== toolName)
      : [...currentTools, toolName];

    setProfileData({
      ...profileData,
      [currentProfile]: { ...currentData, tools: newTools }
    });
  };

  return (
    <div className="mypage-page">
      <div className="mypage-scroll">
        <div className="mypage-top-nav">
          <button className="nav-btn" onClick={() => navigate(-1)}>
            <img src="/left-arrow.png" alt="뒤로" className="nav-icon"/>
          </button>
          <div className="nav-home-icon">
            <img src="/house.png"alt="back-home" className="home-icon"/>
          </div>
        </div>

        <div className="mypage-board">
          <section className="greeting">
            <p className="hello">안녕하세요,</p>
            <h1 className="user-name"><span className="orange-text">두바이쫀득쿠키</span> 님</h1>
            
            <div className="profile-selection">
              <div className="tab-group">
                {profiles.map(p => (
                  <div key={p} className="profile-tab-wrapper">
                    <button 
                      className={`profile-tab ${currentProfile === p ? 'active' : ''}`}
                      onClick={() => setCurrentProfile(p)}
                    >{p}</button>
                    {isEditing && (
                      <span className="delete-x" onClick={(e) => { e.stopPropagation(); setDeleteTarget(p); }}>x</span>
                    )}
                  </div>
                ))}
                {showInput && (
                  <input 
                    className="profile-name-input"
                    value={newProfileName}
                    onChange={(e) => setNewProfileName(e.target.value)}
                    onBlur={handleAddProfile}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddProfile()}
                    autoFocus
                  />
                )}
              </div>
              <button className="add-btn" onClick={() => setShowInput(true)}>
                <img src="add-user.png" alt="add_user" className="add_user-icon"/>
              </button>
            </div>
          </section>
          <div className="scroll-content">
            {['allergies', 'dislikes'].map((type) => (
                <div className="info-card" key={type}>
                <h3 className="card-title">{type === 'allergies' ? '알레르기' : '비선호 음식'}</h3>
                <div className="tag-list">
                    {currentData[type].map(t => (
                    <span key={t} className={`tag ${isEditing ? 'editable' : ''}`} onClick={() => removeTag(type, t)}>
                        #{t} {isEditing && <span className="tag-remove">×</span>}
                    </span>
                    ))}
                    {isEditing && (
                    <div className="tag-add-box">
                        <input 
                        placeholder="입력"
                        value={tagInput.type === type ? tagInput.value : ""}
                        onChange={(e) => setTagInput({ type, value: e.target.value })}
                        onKeyPress={(e) => e.key === 'Enter' && addTag(type)}
                        />
                        <button onClick={() => addTag(type)}>+</button>
                    </div>
                    )}
                </div>
                </div>
            ))}

            <div className="edit-btn-row">
                <button className={`edit-toggle ${isEditing ? 'active' : ''}`} onClick={() => setIsEditing(!isEditing)}>
                {isEditing ? "수정완료" : "수정하기"}
                </button>
            </div>

            <section className="tools-section">
                <h3 className="section-title">주방 및 조리 도구</h3>
                <div className="tool-grid">
                {TOOL_LIST.map(tool => (
                    <div key={tool.name} className="tool-item" onClick={() => toggleTool(tool.name)}>
                        <div className={`tool-box ${currentData.tools.includes(tool.name) ? "selected" : ""}`}>
                        {tool.icon.startsWith("/") ? (
                            <img src={tool.icon} alt={tool.name} className="tool-icon-img" style={tool.size ? { width: tool.size, height: tool.size } : {}} />
                        ) : (
                            tool.icon
                        )}
                        </div>
                        <span className="tool-label">{tool.name}</span>
                    </div>
                ))}
                </div>
            </section>
          </div>
        </div>
      </div>

      {deleteTarget && (
        <div className="modal-overlay">
          <div className="modal-content">
            <p className="modal-text">"{deleteTarget}" 프로필을<br/>삭제하시겠습니까?</p>
            <div className="modal-buttons">
              <button className="modal-btn cancel" onClick={() => setDeleteTarget(null)}>취소</button>
              <button className="modal-btn confirm" onClick={confirmDelete}>삭제</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}