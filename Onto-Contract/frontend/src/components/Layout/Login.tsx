import React, { useState } from 'react';
import { ArrowRight, LockKeyhole, UserCircle } from 'lucide-react';
import { login } from '../../api/client';
import type { UserProfile } from '../../types';

interface LoginProps {
  onLoginSuccess: (user: UserProfile) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('ChangeMe123!');
  const [errorMessage, setErrorMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage('');
    try {
      const user = await login(username, password);
      onLoginSuccess(user);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '登录失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-brand__mark">
            <LockKeyhole size={30} />
          </div>
          <div className="login-brand__title">AI原生合同管理系统</div>
          <div className="login-brand__subtitle">请先登录后进入 AI 原生合同工作台</div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>用户名</span>
            <div className="field-with-icon">
              <UserCircle size={16} />
              <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="请输入用户名" />
            </div>
          </label>

          <label className="form-field">
            <span>密码</span>
            <div className="field-with-icon">
              <LockKeyhole size={16} />
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="请输入密码"
              />
            </div>
          </label>

          {errorMessage ? <div className="form-error">{errorMessage}</div> : null}

          <button className="btn btn-primary login-submit" type="submit" disabled={submitting}>
            {submitting ? '登录中...' : '进入系统'}
            <ArrowRight size={16} />
          </button>
        </form>

        <div className="login-tip">默认账号：admin / 默认密码：ChangeMe123!</div>
      </div>
    </div>
  );
};

export default Login;
