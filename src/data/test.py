# 训练阶段
best_val = 0
global_step = 0
best_accuracy = 0
best_val_f1 = 0  # 记录最好的验证集F1

writer = SummaryWriter('logs')

# 循环训练
for epoch in range(config['epochs']):
    model.train()
    train_loss = 0
    train_correct = 0      # 改为累计正确标签数
    train_total = 0         # 改为累计总标签数
    train_strict_correct = 0  # 累计严格正确样本数
    train_strict_total = 0    # 累计总样本数

    train_process = tqdm(train_loader, desc='Training')

    for image, labels, img_name in train_process:

        image = image.to(device)
        labels = labels.to(device)

        optimizer.zero_grad() # 清空之前的梯度
        outputs = model(image)  # 更换设备运行
        loss = criterion(outputs.logits, labels)  # outputs中包含了多个属性，需要转化成张量

        probability = torch.sigmoid(outputs.logits)
        predict = (probability > 0.5).float()


        # 1. 严格准确率
        # 将预测值和真实值比较，转化成布尔值。
        # 沿着第一维检查是否都为true，然后将每一个八维列表的值统计出来，然后统计全为true的值
        strict_correct = (predict == labels).all(dim=1).sum().item()
        strict_total = labels.size(0)  # 第一维的值，也就是样本数量(也就是batch_size,一个for循环中的样本数量)
        strict_acc = strict_correct / strict_total

        # 2. 宽松准确率
        total_correct = (predict == labels).sum().item()
        total_elements = labels.numel()  # 总元素数(batch_size * 8)
        batch_acc = total_correct / total_elements

        loss.backward()  # 反向传播(计算梯度)
        optimizer.step() # 利用梯度来更新参数，优化

        # 累计损失
        train_loss += loss.item()

        # 累计两种准确率的计数
        train_strict_correct += strict_correct
        train_strict_total += strict_total

        train_correct += total_correct
        train_total += total_elements

        # 在进度条中显示宽松准确率
        train_process.set_postfix({
            'loss': f'{loss.item():.4f}',
            'acc': f'{batch_acc:.3f}',
            'strict': f'{strict_acc:.3f}'
        })

        writer.add_scalar('Batch/Train_Loss', loss.item(), global_step)
        writer.add_scalar('Batch/Train_Strict_Accuracy', strict_acc, global_step)
        writer.add_scalar('Batch/Train_Label_Accuracy', batch_acc, global_step)
        global_step += 1


    # 严格准确率（用于保存最佳模型）
    train_strict_accuracy = train_strict_correct / train_strict_total
    # 宽松准确率（每个标签的准确率）
    train_label_accuracy = train_correct / train_total
    # 平均损失
    avg_train_loss = train_loss / len(train_loader)

    # 记录到TensorBoard
    writer.add_scalar('Loss/Train', avg_train_loss, epoch)
    writer.add_scalar('Accuracy/Train_Strict', train_strict_accuracy, epoch)
    writer.add_scalar('Accuracy/Train_Label', train_label_accuracy, epoch)
    current_lr = optimizer.param_groups[0]['lr']
    writer.add_scalar('Hyperparameters/Learning_Rate', current_lr, epoch)

    print(f"\nEpoch {epoch+1}:")
    print(f"  损失: {avg_train_loss:.4f}")
    print(f"  标签准确率: {train_label_accuracy:.3f} (每个标签)")
    print(f"  严格准确率: {train_strict_accuracy:.3f} (8标签全对)")

    # ========== 验证集评估（添加精确率、召回率、分类准确率） ==========
    model.eval()
    all_val_probs = []
    all_val_labels = []
    val_loss = 0

    with torch.no_grad():
        for val_images, val_labels, _ in val_loader:
            val_images = val_images.to(device)
            val_outputs = model(val_images)  # 更换设备运行
            loss = criterion(val_outputs.logits, val_labels.to(device))
            val_loss += loss.item()
            val_probs = torch.sigmoid(val_outputs.logits).cpu().numpy()  # 转到numpy便于后续使用

            all_val_probs.append(val_probs)
            all_val_labels.append(val_labels.numpy())

    avg_val_loss = val_loss / len(val_loader)
    writer.add_scalar('Loss/Val', avg_val_loss, epoch)

    all_val_probs = np.vstack(all_val_probs)  # 将所有批次的值排成一列存放，因为sklearn期望接受整个数据
    all_val_labels = np.vstack(all_val_labels)

    # 计算验证集预测结果
    # val_preds = (all_val_probs > 0.5).astype(int)  # 将其中>0.5的概率设置为1，反之则为0
    val_preds_fixed = (all_val_probs > 0.5).astype(int)

    # ========== 测试不同阈值 ==========
    print("\n" + "="*60)
    print("不同阈值下的 F1 分数对比")
    print("="*60)

    thresholds = [0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75]
    threshold_f1 = {}

    for th in thresholds:
        preds = (all_val_probs > th).astype(int)
        f1 = f1_score(all_val_labels, preds, average='macro', zero_division=0)
        print(f"阈值 {th}: Macro F1 = {f1:.4f}")

    # ========== 为每个类别找最佳阈值（自适应阈值） ==========
    print("\n" + "="*60)
    print("自适应阈值（每个类别独立）")
    print("="*60)

    best_thresholds = []
    per_class_best_f1 = []

    for i in range(8):
        best_f1 = 0
        best_th = 0.5
        for th in np.arange(0.05, 0.55, 0.02):
            preds = (all_val_probs[:, i] > th).astype(int)
            f1 = f1_score(all_val_labels[:, i], preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_th = th
        best_thresholds.append(best_th)
        per_class_best_f1.append(best_f1)
        print(f"类别 {i}: 最佳阈值={best_th:.2f}, F1={best_f1:.4f}")

    # 使用最佳阈值计算整体 Macro F1
    val_preds_adaptive = np.zeros_like(all_val_probs)
    for i in range(8):
        val_preds_adaptive[:, i] = (all_val_probs[:, i] > best_thresholds[i]).astype(int)

    val_f1_adaptive = f1_score(all_val_labels, val_preds_adaptive, average='macro', zero_division=0)
    val_f1_fixed = threshold_f1.get(0.5, 0)

    print(f"\n自适应阈值 Macro F1: {val_f1_adaptive:.4f}")
    print(f"固定阈值 0.5 Macro F1: {val_f1_fixed:.4f}")
    print(f"改进: {val_f1_adaptive - val_f1_fixed:+.4f}")


    # 1. 分类准确率(正确预测标签数/总标签数)
    # 这个是将预测值和真实值作比较来判断准确率
    val_accuracy = accuracy_score(all_val_labels.flatten(), val_preds_adaptive.flatten())   # flatten():将多维展开成一维

    # 2. 宏平均精确率(预测为正的样本中，实际为正的概率)---(TP/(TP/FP))
    val_precision = precision_score(all_val_labels,val_preds_adaptive, average='macro', zero_division=0)  # macro:注重各类别的平均性能，micro：注重全局平均性能
    # zero_division=0：当没有一个被预测为正样本时返回0

    # 3. 宏平均召回率
    val_recall = recall_score(all_val_labels, val_preds_adaptive, average='macro', zero_division=0)

    # 4. 宏平均F1
    val_f1 = f1_score(all_val_labels, val_preds_adaptive, average='macro', zero_division=0)

    # 5. 各类别单独指标（用于分析少数类）
    per_class_precision = precision_score(all_val_labels, val_preds_adaptive, average=None, zero_division=0)
    per_class_recall = recall_score(all_val_labels, val_preds_adaptive, average=None, zero_division=0)
    per_class_f1 = f1_score(all_val_labels,val_preds_adaptive, average=None, zero_division=0)

    print(f"\n📊 验证集评估结果:")
    print(f"  分类准确率 (Accuracy): {val_accuracy:.4f}")
    print(f"  宏平均精确率 (Precision): {val_precision:.4f}")
    print(f"  宏平均召回率 (Recall): {val_recall:.4f}")
    print(f"  宏平均F1 (Macro F1): {val_f1:.4f}")

    print(f"\n  各类别详细指标:")
    class_names = ['正常', 'DR', '青光眼', '白内障', '黄斑变性', '高血压', '近视', '其他']
    for i in range(8):
        print(f"{class_names[i]}: 精确率={per_class_precision[i]:.3f}, 召回率={per_class_recall[i]:.3f}, F1={per_class_f1[i]:.3f}")


    # 记录到TensorBoard
    writer.add_scalar('Val/Accuracy', val_accuracy, epoch)
    writer.add_scalar('Val/Precision', val_precision, epoch)
    writer.add_scalar('Val/Recall', val_recall, epoch)
    writer.add_scalar('Val/F1', val_f1, epoch)

    # 学习率调度（基于验证F1）
    if scheduler is not None:
        scheduler.step(val_f1)

    # 用验证集F1保存模型
    if val_f1 > best_val_f1:
        best_val_f1 = val_f1
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': avg_train_loss,
            'strict_accuracy': train_strict_accuracy,
            'label_accuracy': train_label_accuracy,
            'val_f1': val_f1,
            'val_accuracy': val_accuracy,
            'val_precision': val_precision,
            'val_recall': val_recall,
            'per_class_f1': per_class_f1,
            'config': config
        }, os.path.join(config['save_dir'], 'best_model_by_val_f1.pth'))
        print(f" 保存验证集最佳模型！F1={val_f1:.4f}")

    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': avg_train_loss,
        'accuracy': train_strict_accuracy,
        'config': config
    }, os.path.join(config['save_dir'], 'latest_model.pth'))

    if train_strict_accuracy > best_accuracy:
        best_accuracy = train_strict_accuracy
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': avg_train_loss,
            'accuracy': train_strict_accuracy,
            'config': config
        }, os.path.join(config['save_dir'], 'best_model.pth'))

writer.close()