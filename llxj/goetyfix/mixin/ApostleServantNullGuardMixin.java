package llxj.goetyfix.mixin;

import com.mega.revelationfix.common.entity.boss.ApostleServant;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * RevelationFix 的 ApostleServant（“使徒”仆从）isAlliedTo 入口空判断（SRG: m_7307_）。
 *
 * 代码形状与 HereticServant / MaverickServant 相同：
 *   ApostleServant.m_7307_(entityIn) 拥有者非空时会以 entityIn 为接收者调用
 *   isAlliedTo，entityIn 为 null 时抛 NPE。
 *
 * 当前不可达：ApostleServant 与父类 Apostle 的 registerGoals 都没有调用
 * HurtByTargetGoal.setAlertOthers（m_26044_），自身不会执行 alertOthers；而
 * alertOthers 只把 null 传给“同精确类”的邻居，所以暂时不会被触发。
 * 本 mixin 作为防御性对齐存在，成本为零（一次判空），避免上游日后开启
 * alertSameType 后重新出现同类崩溃。
 *
 * 未安装 RevelationFix 时，软模式只跳过该 mixin 并告警，不影响启动。
 */
@Mixin(ApostleServant.class)
public class ApostleServantNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
