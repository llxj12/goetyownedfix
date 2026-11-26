package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * 狱焰（HellBlast）爆炸的空主守卫。
 *
 * HellBlast.onHit 会创建一个匿名 SpellExplosion 子类，并把投射物的 owner
 * 捕获进去；子类的 explodeHurt 在结算伤害后会点燃这个 owner：
 *
 *   Entity owner = this.val$entity;              // getOwner()，无主时为 null
 *   if (src.getDirectEntity() instanceof HellBlast hb && hb.getFiery() > 0) {
 *       owner.setSecondsOnFire(5 * hb.getFiery());   // 无主时 NPE，服务端整局崩溃
 *   }
 *
 * 守卫方式：只重定向这一处 Entity.setSecondsOnFire(I) 调用，owner 为 null 时
 * 跳过点燃；先执行的 super.explodeHurt（爆炸伤害）不受影响。
 *
 * 注意不能挂在构造函数 RETURN 上：SpellExplosion 构造函数内部就会调用
 * explodeHurt，异常从构造函数里抛出，RETURN 永远不会执行。
 *
 * 名字使用 intermediary（Fabric 运行时名）：
 *   net.minecraft.class_1297 = Entity
 *   method_5639              = Entity.setSecondsOnFire(int)
 * 目标类 HellBlast$1 是 Goety 自己的类，方法名不会被混淆，保持字面名。
 */
@Mixin(targets = "com.Polarice3.Goety.common.entities.projectiles.HellBlast$1", remap = false)
public class HellBlastExplosionNullGuardMixin {

    @Redirect(
        method = "explodeHurt",
        at = @At(value = "INVOKE", target = "Lnet/minecraft/class_1297;method_5639(I)V"),
        require = 0
    )
    private void goetyownedfix$skipNullOwnerFire(Entity owner, int seconds) {
        if (owner != null) {
            owner.setSecondsOnFire(seconds);
        }
    }
}